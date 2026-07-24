import os
import time
import datetime
import aiohttp
import aiofiles
import asyncio
import logging
import requests
import tgcrypto
import subprocess
import concurrent.futures

from pyrogram import Client
from pyrogram.types import Message


# ================= GLOBAL ================= #

failed_counter = 0


# ================= SAFE DURATION ================= #

def duration(filename):

    try:

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filename
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        try:
            return int(float(result.stdout))
        except:
            return 0

    except:
        return 0


# ================= COMMAND EXEC ================= #

def exec(cmd):

    try:

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output = process.stdout.decode()

        print(output)

        return output

    except Exception as e:

        print(e)

        return ""


# ================= MULTI EXEC ================= #

def pull_run(work, cmds):

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=work
    ) as executor:

        print("Waiting for tasks to complete")

        executor.map(exec, cmds)


# ================= PDF DOWNLOAD ================= #

async def aio(url, name):

    k = f"{name}.pdf"

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                if resp.status == 200:

                    f = await aiofiles.open(k, mode="wb")

                    await f.write(await resp.read())

                    await f.close()

        return k

    except:

        return None


async def download(url, name):

    ka = f"{name}.pdf"

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                if resp.status == 200:

                    f = await aiofiles.open(
                        ka,
                        mode="wb"
                    )

                    await f.write(await resp.read())

                    await f.close()

        return ka

    except:

        return None


# ================= VIDEO INFO ================= #

def parse_vid_info(info):

    info = info.strip()

    info = info.split("\n")

    new_info = []

    temp = []

    for i in info:

        i = str(i)

        if "[" not in i and "---" not in i:

            while "  " in i:
                i = i.replace("  ", " ")

            i.strip()

            i = i.split("|")[0].split(" ", 2)

            try:

                if (
                    "RESOLUTION" not in i[2]
                    and i[2] not in temp
                    and "audio" not in i[2]
                ):

                    temp.append(i[2])

                    new_info.append((i[0], i[2]))

            except:
                pass

    return new_info


def vid_info(info):

    info = info.strip()

    info = info.split("\n")

    new_info = dict()

    temp = []

    for i in info:

        i = str(i)

        if "[" not in i and "---" not in i:

            while "  " in i:
                i = i.replace("  ", " ")

            i.strip()

            i = i.split("|")[0].split(" ", 3)

            try:

                if (
                    "RESOLUTION" not in i[2]
                    and i[2] not in temp
                    and "audio" not in i[2]
                ):

                    temp.append(i[2])

                    new_info.update(
                        {
                            f"{i[2]}": f"{i[0]}"
                        }
                    )

            except:
                pass

    return new_info


# ================= RUN ================= #

async def run(cmd):

    try:

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        print(f"[{cmd!r} exited with {proc.returncode}]")

        if proc.returncode == 1:
            return False

        if stdout:
            return f"[stdout]\n{stdout.decode()}"

        if stderr:
            return f"[stderr]\n{stderr.decode()}"

    except Exception as e:

        return str(e)


# ================= OLD DOWNLOAD ================= #

def old_download(url, file_name, chunk_size=1024 * 10):

    try:

        if os.path.exists(file_name):
            os.remove(file_name)

        r = requests.get(
            url,
            allow_redirects=True,
            stream=True
        )

        with open(file_name, "wb") as fd:

            for chunk in r.iter_content(
                chunk_size=chunk_size
            ):

                if chunk:
                    fd.write(chunk)

        return file_name

    except:

        return None


# ================= HUMAN SIZE ================= #

def human_readable_size(size, decimal_places=2):

    for unit in [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
        "PB"
    ]:

        if size < 1024.0 or unit == "PB":
            break

        size /= 1024.0

    return f"{size:.{decimal_places}f} {unit}"


# ================= TIME NAME ================= #

def time_name():

    date = datetime.date.today()

    now = datetime.datetime.now()

    current_time = now.strftime("%H%M%S")

    return f"{date} {current_time}.mp4"


# ================= VIDEO DOWNLOAD ================= #

async def download_video(url, cmd, name):

    global failed_counter

    download_cmd = (
        f'{cmd} '
        f'-R 50 '
        f'--fragment-retries 50 '
        f'--external-downloader aria2c '
        f'--downloader-args "aria2c: -x 16 -j 32 -s 16" '
        f'--socket-timeout 30 '
        f'--retry-sleep 5'
    )

    print(download_cmd)

    logging.info(download_cmd)

    try:

        k = subprocess.run(
            download_cmd,
            shell=True
        )

        if (
            "visionias" in cmd
            and k.returncode != 0
            and failed_counter <= 10
        ):

            failed_counter += 1

            await asyncio.sleep(5)

            return await download_video(
                url,
                cmd,
                name
            )

        failed_counter = 0

        possible_files = [
            name,
            f"{name}.mp4",
            f"{name}.mkv",
            f"{name}.webm",
            f"{name}.mp4.webm"
        ]

        for file in possible_files:

            if os.path.isfile(file):

                if os.path.getsize(file) > 0:
                    return file

        return None

    except Exception as e:

        print(e)

        return None


# ================= SEND DOC ================= #

async def send_doc(
    bot: Client,
    m: Message,
    cc,
    ka,
    cc1,
    prog,
    count,
    name
):

    reply = await m.reply_text(
        f"📤 Uploading » `{name}`"
    )

    await asyncio.sleep(1)

    try:

        await m.reply_document(
            ka,
            caption=cc1
        )

    except Exception as e:

        await m.reply_text(
            f"❌ Upload Failed\n\n{str(e)}"
        )

    try:
        await reply.delete(True)
    except:
        pass

    try:
        os.remove(ka)
    except:
        pass

    await asyncio.sleep(2)


# ================= SEND VIDEO ================= #

async def send_vid(
    bot: Client,
    m: Message,
    cc,
    filename,
    thumb,
    name,
    prog
):

    try:

        subprocess.run(
            f'ffmpeg -i "{filename}" '
            f'-ss 00:00:05 '
            f'-vframes 1 '
            f'"{filename}.jpg"',
            shell=True
        )

    except:
        pass

    try:
        await prog.delete(True)
    except:
        pass

    reply = await m.reply_text(
        f"📤 Uploading » `{name}`"
    )

    try:

        if thumb == "no":

            if os.path.exists(f"{filename}.jpg"):
                thumbnail = f"{filename}.jpg"
            else:
                thumbnail = None

        else:

            thumbnail = thumb

    except:

        thumbnail = None

    dur = duration(filename)

    try:

        await m.reply_video(
            video=filename,
            caption=cc,
            supports_streaming=True,
            thumb=thumbnail,
            duration=dur
        )

    except Exception:

        try:

            await m.reply_document(
                document=filename,
                caption=cc
            )

        except Exception as e:

            await m.reply_text(
                f"❌ Upload Failed\n\n{str(e)}"
            )

    # ========= CLEANUP ========= #

    try:
        os.remove(filename)
    except:
        pass

    try:
        os.remove(f"{filename}.jpg")
    except:
        pass

    try:
        await reply.delete(True)
    except:
        pass
