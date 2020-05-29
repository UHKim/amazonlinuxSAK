import sys
import subprocess
import os
import video_cmds
import argparse

parser = argparse.ArgumentParser(description='Process some video.')

parser.add_argument('--tid', type=str, required=True, help='task id')
parser.add_argument('--vid', type=str, required=True, help='visualVideo id')
parser.add_argument('--s3s', type=str, required=True, help='s3 src')
parser.add_argument('--s3d', type=str, required=True, help='s3 dst')
parser.add_argument('--ss', type=str, required=False,
                    default="00:00:01", help='src slice start timecode')
parser.add_argument('--dd', type=str, required=False,
                    help='src slice end timecode')

args = parser.parse_args()

task_id = args.tid
src_s3_path = args.s3s
dst_s3_path = args.s3d
start_timecode = args.ss
end_timecode = args.dd

vid = args.vid
vid_sns_arn = os.environ["SNS_VIDEO_UPDATED_EVENT_ARN"]

file_max_length = 300


archive_config = [
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

working_directory = "/tmp/decode/" + task_id

log_folder = working_directory + "/log"
hls_folder = working_directory + "/hls"


def setup():
    os.makedirs(working_directory)

    os.makedirs(log_folder)
    os.makedirs(hls_folder)


def archive_upload():
    print("========== import s3 folder ===========")

    video_cmds.sync_aws_s3(src_s3_path, working_directory)
    slice_files = os.listdir(working_directory)
    slice_files.sort()

    print(slice_files)

    print("========== concat sliced pieces ===========")

    video_cmds.generate_input_file_list(
        slice_files, working_directory + "/input")
    video_cmds.ffmpeg_merge(working_directory + "/input",
                            working_directory + "/output.ts",
                            log_folder + "/merge")

    video_cmds.cmd_popen("rm -rf %s" % (working_directory + "/input"))

    print("========== generate hls ===========")

    data = video_cmds.ffmpeg_hls_convert(
        working_directory + "/output.ts",
        hls_folder,
        archive_config,
        log_folder + "/hls_convert"
    )

    print("========== export s3 result folder ===========")

    video_cmds.hls_playlist_file(working_directory + "/hls")
    video_cmds.sync_aws_s3(hls_folder, dst_s3_path + "/hls")

    video_cmds.cmd_popen("rm -rf %s" % (working_directory))

    if (vid):
        video_cmds.aws_cli_publish_vV_sns(
            vid_sns_arn, "ARCHIVE_COMPLETE_UPLOAD", vid)


setup()
archive_upload()
