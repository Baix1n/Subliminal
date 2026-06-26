#!/usr/bin/env python3
import argparse
import math
import wave
from pathlib import Path

import numpy as np


def read_wav(path, target_rate):
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.getnframes()
        raw = wav.readframes(frames)

    if sample_width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128) / 128
    elif sample_width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
    elif sample_width == 3:
        bytes_ = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        signed = (
            bytes_[:, 0].astype(np.int32)
            | (bytes_[:, 1].astype(np.int32) << 8)
            | (bytes_[:, 2].astype(np.int32) << 16)
        )
        signed = np.where(signed & 0x800000, signed - 0x1000000, signed)
        data = signed.astype(np.float32) / 8388608
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648
    else:
        raise ValueError(f"{path} 的 WAV 位深不支持：{sample_width * 8} bit")

    data = data.reshape(-1, channels)
    if sample_rate != target_rate:
        data = resample(data, sample_rate, target_rate)
    return np.clip(data, -1, 1).astype(np.float32)


def resample(data, source_rate, target_rate):
    if len(data) == 0:
        return data
    new_len = max(1, int(round(len(data) * target_rate / source_rate)))
    old_x = np.linspace(0, len(data) - 1, num=len(data), dtype=np.float64)
    new_x = np.linspace(0, len(data) - 1, num=new_len, dtype=np.float64)
    channels = [np.interp(new_x, old_x, data[:, channel]) for channel in range(data.shape[1])]
    return np.stack(channels, axis=1).astype(np.float32)


def mono(data):
    return data[:, 0] if data.shape[1] == 1 else data.mean(axis=1)


def stereo(data):
    if data.shape[1] == 1:
        return data[:, 0], data[:, 0]
    return data[:, 0], data[:, 1]


def loop_slice(channel, start, count):
    indices = (np.arange(start, start + count, dtype=np.int64) % len(channel))
    return channel[indices]


def soft_clip(values):
    return np.tanh(values * 0.95) / np.tanh(0.95)


def parse_frequencies(value):
    if not value.strip():
        return []
    frequencies = []
    for item in value.replace("，", ",").split(","):
        item = item.strip()
        if item:
            frequency = float(item)
            if frequency <= 0 or frequency > 20000:
                raise ValueError(f"频率超出范围：{frequency}")
            frequencies.append(frequency)
    return frequencies


def apply_voice_speed(source, speed):
    if speed <= 0:
        raise ValueError("人声倍速必须大于 0。")
    if abs(speed - 1) < 0.0001:
        return source
    new_len = max(1, int(round(len(source) / speed)))
    old_x = np.arange(len(source), dtype=np.float64)
    new_x = np.arange(new_len, dtype=np.float64) * speed
    return np.interp(new_x, old_x, source).astype(np.float32)


def build_layered_voice_loop(voice, layer_count, sample_rate, voice_speed=1, stereo_width=1, layer_spacing=0.37):
    source = mono(voice).astype(np.float32)
    source = apply_voice_speed(source, voice_speed)
    frames = len(source)
    if frames == 0:
        raise ValueError("人声文件为空。")

    stereo_width = min(1, max(0, stereo_width))
    layer_spacing = max(0.01, layer_spacing)
    layers = np.arange(layer_count, dtype=np.float64)
    offsets = np.floor((layers * layer_spacing + (np.mod(layers, 3) * layer_spacing * 0.31)) * sample_rate).astype(np.int64) % frames
    pan = np.zeros(layer_count, dtype=np.float64) if layer_count == 1 else ((layers / (layer_count - 1)) * 2 - 1) * stereo_width
    left_gain = np.sqrt((1 - pan) / 2)
    right_gain = np.sqrt((1 + pan) / 2)

    kernel_left = np.zeros(frames, dtype=np.float32)
    kernel_right = np.zeros(frames, dtype=np.float32)
    kernel_indices = (-offsets) % frames
    np.add.at(kernel_left, kernel_indices, left_gain.astype(np.float32))
    np.add.at(kernel_right, kernel_indices, right_gain.astype(np.float32))

    normalizer = math.sqrt(layer_count)
    source_fft = np.fft.rfft(source)
    left = np.fft.irfft(source_fft * np.fft.rfft(kernel_left), n=frames).astype(np.float32) / normalizer
    right = np.fft.irfft(source_fft * np.fft.rfft(kernel_right), n=frames).astype(np.float32) / normalizer
    return left, right


def frequency_slice(frequencies, start, count, sample_rate):
    if not frequencies:
        return np.zeros(count, dtype=np.float32)
    frames = np.arange(start, start + count, dtype=np.float64)
    tone = np.zeros(count, dtype=np.float64)
    for frequency in frequencies:
        tone += np.sin((2 * np.pi * frequency * frames) / sample_rate)
    return (tone / len(frequencies)).astype(np.float32)


def fade_slice(start, count, total_frames, fade_frames):
    if fade_frames <= 0:
        return np.ones(count, dtype=np.float32)
    frames = np.arange(start, start + count, dtype=np.float32)
    fade = np.minimum(1, frames / fade_frames)
    fade = np.minimum(fade, (total_frames - frames) / fade_frames)
    return np.clip(fade, 0, 1).astype(np.float32)


def write_chunk(wav, left, right):
    interleaved = np.empty(left.size * 2, dtype="<i2")
    interleaved[0::2] = (np.clip(left, -1, 1) * 32767).astype("<i2")
    interleaved[1::2] = (np.clip(right, -1, 1) * 32767).astype("<i2")
    wav.writeframes(interleaved.tobytes())


def generate(args, progress=None):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.name}.wav"

    voice = read_wav(Path(args.voice_file), args.sample_rate)
    voice_left, voice_right = build_layered_voice_loop(
        voice,
        args.voice_layers,
        args.sample_rate,
        args.voice_speed,
        args.voice_stereo_width,
        args.layer_spacing,
    )

    music = read_wav(Path(args.music_file), args.sample_rate) if args.music_file else None
    noise = read_wav(Path(args.noise_file), args.sample_rate) if args.noise_file else None
    music_left, music_right = stereo(music) if music is not None else (None, None)
    noise_left, noise_right = stereo(noise) if noise is not None else (None, None)

    frequencies = parse_frequencies(args.frequencies)
    total_frames = int(args.minutes * 60 * args.sample_rate)
    fade_frames = int(args.fade_seconds * args.sample_rate)
    chunk_frames = int(args.chunk_seconds * args.sample_rate)

    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(args.sample_rate)

        for start in range(0, total_frames, chunk_frames):
            count = min(chunk_frames, total_frames - start)
            left = loop_slice(voice_left, start, count) * args.voice_volume
            right = loop_slice(voice_right, start, count) * args.voice_volume

            if music is not None:
                left += loop_slice(music_left, start, count) * args.music_volume
                right += loop_slice(music_right, start, count) * args.music_volume
            if noise is not None:
                left += loop_slice(noise_left, start, count) * args.noise_volume
                right += loop_slice(noise_right, start, count) * args.noise_volume
            if frequencies and args.tone_volume > 0:
                tone = frequency_slice(frequencies, start, count, args.sample_rate) * args.tone_volume
                left += tone
                right += tone

            fade = fade_slice(start, count, total_frames, fade_frames)
            write_chunk(wav, soft_clip(left * fade * 0.86), soft_clip(right * fade * 0.86))
            if progress:
                progress(min(1, (start + count) / total_frames))

    print(f"已生成：{output_path}")
    print(f"人声层数：{args.voice_layers}")
    affirmations_text = getattr(args, "affirmations_text", "")
    if affirmations_text:
        text_path = output_dir / f"{args.name}_affirmations.txt"
        text_path.write_text(affirmations_text.rstrip() + "\n", encoding="utf-8")
        print(f"文案已保存：{text_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="本地生成 subliminal WAV，支持高密度人声叠层。")
    parser.add_argument("--voice-file", required=True, help="肯定句人声 WAV 文件。")
    parser.add_argument("--music-file", help="背景音乐 WAV 文件，可选。")
    parser.add_argument("--noise-file", help="白噪音 WAV 文件，可选。")
    parser.add_argument("--name", default="my_sub", help="输出文件名，不含扩展名。")
    parser.add_argument("--output-dir", default="outputs", help="输出目录。")
    parser.add_argument("--minutes", type=float, default=10, help="输出时长，单位分钟。")
    parser.add_argument("--voice-layers", type=int, default=3, help="人声叠加层数，可以设为 10000。")
    parser.add_argument("--voice-volume", type=float, default=0.055, help="人声音量。上万层建议从 0.01 到 0.03 试。")
    parser.add_argument("--voice-speed", type=float, default=1, help="人声倍速，0.5 表示半速，2 表示两倍速。")
    parser.add_argument("--voice-stereo-width", type=float, default=1, help="人声声像宽度，0 为居中，1 为左右铺满。")
    parser.add_argument("--layer-spacing", type=float, default=0.37, help="每层人声错开的秒数，越小越密。")
    parser.add_argument("--music-volume", type=float, default=0.8, help="背景音乐音量。")
    parser.add_argument("--noise-volume", type=float, default=0.35, help="白噪音音量。")
    parser.add_argument("--fade-seconds", type=float, default=6, help="淡入淡出秒数。")
    parser.add_argument("--frequencies", default="", help="逗号分隔的频率，例如 528,639。")
    parser.add_argument("--tone-volume", type=float, default=0, help="频率正弦音量。")
    parser.add_argument("--sample-rate", type=int, default=44100, help="输出采样率。")
    parser.add_argument("--chunk-seconds", type=float, default=10, help="分块写入秒数。")
    parser.add_argument("--affirmations-text", default="", help="同时保存的肯定句文本。")
    args = parser.parse_args()

    if args.voice_layers < 1:
        parser.error("--voice-layers 必须大于等于 1")
    if args.voice_layers > 100000:
        parser.error("--voice-layers 太高了，建议不超过 100000")
    if args.voice_speed <= 0:
        parser.error("--voice-speed 必须大于 0")
    if args.voice_stereo_width < 0 or args.voice_stereo_width > 1:
        parser.error("--voice-stereo-width 必须在 0 到 1 之间")
    if args.layer_spacing <= 0:
        parser.error("--layer-spacing 必须大于 0")
    if args.minutes <= 0:
        parser.error("--minutes 必须大于 0")
    if args.chunk_seconds <= 0:
        parser.error("--chunk-seconds 必须大于 0")

    generate(args)


if __name__ == "__main__":
    main()
