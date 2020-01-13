
import logging , re, os
from itertools import chain, filterfalse, starmap
from collections import namedtuple
from config import COURSES, BASE_DOWNLOAD_PATH


HEADERS = {
'Content-Type': 'application/json',
'user-agent': 'Mozilla/5.0'
        }

session = None
FILE_TYPE_VIDEO = ".mp4"
FILE_TYPE_SUBTITLE = ".srt"

Course = namedtuple("Course", ["name", "slug", "description", "unlocked", "chapters"])
Chapter = namedtuple("Chapter", ["name", "videos", "index"])
Video = namedtuple("Video", ["name", "slug", "index", "filename"])

def sub_format_time(ms):
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02}:{minutes:02}:{seconds:02},{milliseconds:02}'

def clean_dir_name(dir_name):
    # Remove starting digit and dot (e.g '1. A' -> 'A')
    # Remove bad characters         (e.g 'A: B' -> 'A B')
    no_digit = re.sub(r'^\d+\.', "", dir_name)
    no_bad_chars = re.sub(r'[\\:<>"/|?*]', "", no_digit)
    return no_bad_chars.strip()

def chapter_dir(course: Course, chapter: Chapter):
    folder_name = f"{str(chapter.index).zfill(2)} - {clean_dir_name(chapter.name)}"
    if folder_name == '01 - ':folder_name = '01 - Welcome'
    chapter_path = os.path.join(BASE_DOWNLOAD_PATH, clean_dir_name(course.name), folder_name)
    return chapter_path

def build_course(course_element: dict):
    chapters = [
        Chapter(name=course['title'],
                videos=[
                    Video(name=video['title'],
                          slug=video['slug'],
                          index=idx,
                          filename=f"{str(idx).zfill(2)} - {clean_dir_name(video['title'])}{FILE_TYPE_VIDEO}"
                          )
                    for idx, video in enumerate(course['videos'], start=1)
                ],index=idx)
        for idx, course in enumerate(course_element['chapters'], start=1)
    ]
    course = Course(name=course_element['title'],
                    slug=course_element['slug'],
                    description=course_element['description'],
                    unlocked=course_element['fullCourseUnlocked'],
                    chapters=chapters)
    return course

def fetch_courses(sess):
    global session
    session = sess
    for course in COURSES:
        fetch_course(course)

def fetch_course(course_slug):
    url = f"https://www.linkedin.com/learning-api/detailedCourses??fields=fullCourseUnlocked,releasedOn,exerciseFileUrls,exerciseFiles&" \
          f"addParagraphsToTranscript=true&courseSlug={course_slug}&q=slugs"
    HEADERS['Csrf-Token'] = session.cookies._cookies['.www.linkedin.com']['/']['JSESSIONID'].value.replace('"','')

    resp = session.get(url, headers=HEADERS)
    
    data = resp.json()
    course = build_course(data['elements'][0])

    logging.info(f'[*] Fetching course {course.name}')

    fetch_chapters(course)
    logging.info(f'[*] Finished fetching course "{course.name}"')



def fetch_chapters(course: Course):
    chapters_dirs = [chapter_dir(course, chapter) for chapter in course.chapters]

    # Creating all missing directories
    missing_directories = filterfalse(os.path.exists, chapters_dirs)
    for d in missing_directories:
        os.makedirs(d)

    for chapter in course.chapters:
        fetch_chapter(course, chapter)


def fetch_chapter(course: Course, chapter: Chapter):
    for video in chapter.videos :
        fetch_video(course, chapter, video)

def fetch_video(course: Course, chapter: Chapter, video: Video):
    subtitles_filename = os.path.splitext(video.filename)[0] + FILE_TYPE_SUBTITLE
    video_file_path = os.path.join(chapter_dir(course, chapter), video.filename)
    subtitle_file_path = os.path.join(chapter_dir(course, chapter), subtitles_filename)
    video_exists = os.path.exists(video_file_path)
    subtitle_exists = os.path.exists(subtitle_file_path)
    if video_exists and subtitle_exists:
        return

    logging.info(f"[~] Fetching course '{course.name}' Chapter no. {chapter.index} Video no. {video.index}")
    
    video_url = f'https://www.linkedin.com/learning-api/detailedCourses?addParagraphsToTranscript=false&courseSlug={course.slug}&q=slugs&resolution=_720&videoSlug={video.slug}'
    data = None
    tries = 3
    for _ in range(tries):
        try:
            resp = session.get(video_url,  headers=HEADERS)
            data = resp.json()
            resp.raise_for_status()
            break
        except :
            pass

    video_url = data['elements'][0]['selectedVideo']['url']['progressiveUrl']
    
    try:
        subtitles = data['elements'][0]['selectedVideo']['transcript']
    except Exception as e:
        print(e)
        subtitles = None
    duration_in_ms = int(data['elements'][0]['selectedVideo']['durationInSeconds']) * 1000

    if not video_exists:
        logging.info(f"[~] Writing {video.filename}")
        download_file(video_url, video_file_path)

    if subtitles is not None:
        logging.info(f"[~] Writing {subtitles_filename}")
        subtitle_lines = subtitles['lines']            
        write_subtitles(subtitle_lines, subtitle_file_path, duration_in_ms)

    logging.info(f"[~] Done fetching course '{course.name}' Chapter no. {chapter.index} Video no. {video.index}")


def write_subtitles(subs, output_path, video_duration):
    def subs_to_lines(idx, sub):
        starts_at = sub['transcriptStartAt']
        ends_at = subs[idx]['transcriptStartAt'] if idx < len(subs) else video_duration
        caption = sub['caption']
        return f"{idx}\n" \
               f"{sub_format_time(starts_at)} --> {sub_format_time(ends_at)}\n" \
               f"{caption}\n\n"

    with open(output_path, 'wb') as f:
        for line in starmap(subs_to_lines, enumerate(subs, start=1)):
            f.write(line.encode('utf8'))


def download_file(url, output):
    with session.get(url, headers=HEADERS, allow_redirects=True) as r:
        try:
            open(output, 'wb').write(r.content)
            # with open(output, 'wb') as f:
            #     while True:
            #         chunk = r.content.read(1024)
            #         if not chunk:
            #             break
            #         f.write(chunk)
        except Exception as e:
            logging.exception(f"[!] Error while downloading: '{e}'")
            if os.path.exists(output):
                os.remove(output)







