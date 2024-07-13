#!/usr/bin/env python
import os
import glob
import subprocess
from concurrent.futures import ThreadPoolExecutor

def convert_file(filename, crf, speed, quality, encode):
    base = os.path.splitext(filename)[0]
    print(f"Starting conversion of {filename}...")

    # Determine if additonal subtitles are found
    subtitle_file = f"{base}.vtt"
    subtitle_opts = []
    if os.path.isfile(subtitle_file):
        print(f"Subtitle file found: {subtitle_file}")
        subtitle_opts = ["-vf", f"subtitles='{subtitle_file}'"]
    else:
        print(f"No matching subtitle file found for {filename}.")

    # Determine if additonal audio tracks are found
    audio_track_files = glob.glob(f"{base}*.mka")
    audio_tracks = []
    for audio_track_file in audio_track_files:
        if base in audio_track_file:
            print(f"Additional audio track found: {audio_track_file}")
            audio_tracks.extend(["-i", audio_track_file])
        else:
            print(f"Ignored non-matching audio track: {audio_track_file}")

    # ffmpeg command for conversion
    new_file_name = f"{base}-converted.mkv"

    # Configure video codec parameters based on the encoding method
    if encode == 'h264_nvenc':
        ffmpeg_command = [
            "ffmpeg",
            "-i", filename,
            *audio_tracks,
            *subtitle_opts,
            "-c:v", "hevc_nvenc",
            "-b:v", "1.25M",
            "-maxrate", "1.25M",
            "-bufsize", "2.25M",
            "-preset", speed,
            "-pix_fmt", "p010le",
            "-profile:v", "main10",
            "-tier", "high",
            "-refs", "3",
            "-coder", "1",
            "-rc", "vbr_hq",
            "-rc-lookahead", "32",
            "-bf", "3",
            "-b_ref_mode", "middle",
            "-b_strategy", "1",
            "-r", "24000/1001",
            "-c:a", "ac3",
            "-b:a", "192K",
            "-loglevel", "info"
        ]
    else:
        ffmpeg_command = [
            "ffmpeg",
            "-i", filename,
            *audio_tracks,
            "-map", "0",
            "-map", "-0:a",
            *subtitle_opts,
            "-c:a", "ac3",
            "-b:a", "192k",
            "-c:s", "copy",
            "-c:v", "libx265",
            "-preset", speed,
            "-x265-params", "aq-mode=3:deblock=-1,-1:vbv-bufsize=2250:vbv-maxrate=1250",
            "-crf", str(crf),
            "-loglevel", "info",
            "-pix_fmt", "yuv420p10le"
        ]
        if quality == '5':
            ffmpeg_command += ["-tune", "animation"]

    ffmpeg_command.append(new_file_name)
    print(ffmpeg_command)
    subprocess.run(ffmpeg_command)

    # Automatic removal of original video, audio, and subtitles.
    if os.path.isfile(new_file_name):
        print(f"Finished converting {filename}. \nRemoving original file, audio tracks, and subtitle file")
        os.remove(filename)
        if os.path.isfile(subtitle_file):
            os.remove(subtitle_file)
        for audio_track_file in audio_track_files:
            if base in audio_track_file and os.path.isfile(audio_track_file):
                os.remove(audio_track_file)
        final_file_name = f"{base}.mkv"
        os.rename(new_file_name, final_file_name)
        print(f"Renamed '{new_file_name}' to '{final_file_name}'.")
    else:
        print(f"Conversion failed for {filename}.")

def find_files():
    files = []
    for ext in ['*.mkv', '*.mp4']:
        files.extend(glob.glob(f'**/{ext}', recursive=True))
    return files

def main():
    print("Select Encoding Method\n1. Nvidia\n2. CPU")
    user_choice = input("Enter your choice: ")
    valid_encode = {'1': 'h264_nvenc', '2': 'libx265'}
    encode = valid_encode.get(user_choice)
    if encode is None:
        print("Invalid Encoding Selection")
        return

    if encode == 'h264_nvenc':
        print("Select media type:\n1. UHD (Ultra High Definition)\n2. BRD (Blu-ray Disc)\n3. DVD High\n4. DVD Low")
        quality_options = {'1', '2', '3', '4'}
    else:
        print("Select media type:\n1. UHD (Ultra High Definition)\n2. BRD (Blu-ray Disc)\n3. DVD High\n4. DVD Low\n5. Animation")
        quality_options = {'1', '2', '3', '4', '5'}

    quality = input("Enter your choice: ")
    crf_values = {'1': 12, '2': 18, '3': 20, '4': 25, '5': 18}
    crf = crf_values.get(quality)
    if quality not in quality_options:
        print("Invalid selection. Please choose from the available options")
        return

    print("\nEnter speed setting (slow, medium, fast, hp, hq, ll, llhq, llhp, lossless, losslesshp):")
    speed = input("Enter your choice: ")
    valid_speeds = {'slow', 'medium', 'fast', 'hp', 'hq', 'bd', 'll', 'llhq', 'llhp', 'lossless', 'losslesshp'}
    if speed not in valid_speeds:
        print("Invalid speed setting.")
        return

    if encode == 'h264_nvenc':
        workers = 1
    else:
        print("Max Workers")
        workers = int(input("Enter Total Workers: ")) 

    files = find_files()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(convert_file, file, crf, speed, quality, encode) for file in files]
        for future in futures:
            future.result()

if __name__ == '__main__':
    main()
