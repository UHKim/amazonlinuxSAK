import subprocess
import math

default_config = [
    {
        "height": 480,
        "audio_rate": 128,
        "min_rate": 1400,
        "max_rate": 1498,
        "buf_size": 2100,
    },
    {
        "height": 720,
        "audio_rate": 128,
        "min_rate": 2800,
        "max_rate": 2996,
        "buf_size": 4200,
    },
    {
        "height": 1080,
        "audio_rate": 192,
        "min_rate": 5000,
        "max_rate": 5350,
        "buf_size": 7500,
    }
]


def cmd_popen(cmd):
    print("executing cmd: %s " % (cmd))
    data = subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True).wait()
    return data


def cmd_check_output(cmd):
    data = subprocess.check_output(cmd, shell=True)
    return data


def sync_aws_s3(src, dst):
    cmd = "aws s3 sync %s %s" % (src, dst)
    print(cmd)
    data = cmd_popen(cmd)
    return data


def aws_cli_publish_vV_sns(sns_arn, category, vId):
    cmd = 'aws sns publish --topic-arn "%s" --message %s --message-attributes "category={DataType=String,StringValue=%s},visualVideoId={DataType=String,StringValue=%s}"' % (
        sns_arn, vId, category, vId)
    data = cmd_popen(cmd)
    return data


def detect_black_frames(file, dst="blackdetect.txt"):
    cmd = (
        'ffmpeg -i %s -vf "blackdetect=d=2:pix_th=0.05" -an -f null - 2>&1 | grep blackdetect > %s'
        % (file, dst)
    )
    data = cmd_popen(cmd)

    start_time = 0

    if data == 0:
        f = open(dst, "r")
        while True:
            line = f.readline()
            if not line:
                break
            if "blackdetect" in line:
                start_black_string = line.split()[3].split(":")[1]
                start_time = round(float(start_black_string))
            else:
                continue

        f.close()

        return start_time
    else:
        return 0


def convert_timecode_to_string(timecode):
    split_string = timecode.split(':')
    hours = int(split_string[0]) * 3600
    mins = int(split_string[1]) * 60
    secs = int(split_string[2])

    return hours + mins + secs


def convert_seconds_to_timecode(sec):
    hours = math.floor(sec / 3600)
    mins = math.floor(sec / 60) % 60
    secs = sec % 60

    return "%02d:%02d:%02d" % (hours, mins, secs)


def generate_input_file_list(files, dst):
    file_string = ""
    for idx, file in enumerate(files):
        if (".ts" in file) or (".mov" in file) or (".mkv" in file) or (".mp4" in file) or (".avi" in file):
            file_string = file_string + \
                "%sfile %s" % (idx != 0 and "\n" or "", file)

    with open(dst, "w") as f:
        f.write(file_string)


def ffmpeg_merge(input_file_list, dst, log_dst="/tmp/log/merge"):
    cmd = "ffmpeg -f concat -i %s -c copy %s > %s" % (
        input_file_list, dst, log_dst)

    f = open(log_dst, 'w')
    f.close()

    data = cmd_popen(cmd)
    return data


def ffmpeg_range(src, start, duration, dst, log_dst="/tmp/log/range"):
    cmd = "ffmpeg -i %s -ss %s -t %s -c copy %s > %s" % (
        src, start, duration, dst, log_dst)

    f = open(log_dst, 'w')
    f.close()

    data = cmd_popen(cmd)
    return data


def ffmpeg_hls_convert(src, dst="/tmp/hls", hls_configs=default_config, log_dst="/tmp/log/hls_convert"):
    f = open(log_dst, 'w')
    f.close()

    config_cmd = ""
    for hls_config in hls_configs:
        print(hls_config)
        height = hls_config["height"]
        config_cmd = (
            config_cmd
            + "-vf scale=-2:%d -c:a aac -ar 48000 -c:v h264 -profile:v main -crf 20 -sc_threshold 0 -g 48 -keyint_min 48 -hls_time 4 -hls_playlist_type vod -b:v %dk -maxrate %dk -bufsize %dk -b:a %dk -hls_segment_filename %s/%dp_%s %s/%dp.m3u8 "
            % (
                height,
                hls_config["min_rate"],
                hls_config["max_rate"],
                hls_config["buf_size"],
                hls_config["audio_rate"],
                dst,
                height,
                "%04d.ts",
                dst,
                height,
            )
        )
    cmd = "ffmpeg -hide_banner -y -i %s -threads 0 -max_muxing_queue_size 9999 %s > %s" % (
        src,
        config_cmd,
        log_dst,
    )

    data = cmd_popen(cmd)

    return data


def hls_playlist_file(dst, hls_configs=default_config):
    file_string = "#EXTM3U\n#EXT-X-VERSION:3"
    for hls_config in hls_configs:
        file_string = file_string + "\n#EXT-X-STREAM-INF:BANDWIDTH=%d\n%sp.m3u8" % (
            hls_config["min_rate"] * 1000,
            hls_config["height"],
        )

    with open(dst + "/playlist.m3u8", "w") as f:
        f.write(file_string)
