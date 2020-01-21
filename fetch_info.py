
import logging , re, os 
from itertools import chain, filterfalse, starmap
from collections import namedtuple
from clint.textui import progress

BASE_DOWNLOAD_PATH = os.path.join(os.path.dirname(__file__), "downloads")

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
    logging.info(f'[*] Fetching course {course_element["title"]} Exercise Files')    
    if course_element.get('exerciseFiles',''):
        chapter_path = os.path.join(BASE_DOWNLOAD_PATH, clean_dir_name(course_element['title']), 'Exercise Files')

        if not os.path.exists(chapter_path) : os.makedirs(chapter_path)
        for exercise in course_element['exerciseFiles']:
            file_name = exercise['name']
            file_link = exercise['url']
            logging.info(f'[~] writing course {course_element["title"]} Exercise Files')
            download_file(file_link, os.path.join(chapter_path,file_name))
            logging.info(f'[*] Finished writing course {course_element["title"]} Exercise Files')
    course = Course(name=course_element['title'],
                    slug=course_element['slug'],
                    description=course_element['description'],
                    unlocked=course_element['fullCourseUnlocked'],
                    chapters=chapters)
    return course

def fetch_courses(sess,COURSES):
    global session
    session = sess
    for course in COURSES:
        if not course:continue
        if 'learning/' in course :
            splitted = course.split('learning/')[1]
            course = splitted.split('/')[0] if '/' in splitted else splitted        
        fetch_course(course)

def fetch_course(course_slug):
    url = f"https://www.linkedin.com/learning-api/detailedCourses??fields=fullCourseUnlocked,releasedOn,exerciseFileUrls,exerciseFiles&" \
          f"addParagraphsToTranscript=true&courseSlug={course_slug}&q=slugs"
    HEADERS['Csrf-Token'] = session.cookies._cookies['.www.linkedin.com']['/']['JSESSIONID'].value.replace('"','')
    
    resp = session.get(url, headers=HEADERS)
    if resp.status_code == 429 :
        logging.info(f'[!] Faild due to: {resp.reason}')
        return
    data = resp.json()
    

    # data['elements'][0]['exerciseFiles']

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
    try:
        video_url = data['elements'][0]['selectedVideo']['url']['progressiveUrl']
    except :
        logging.error("Extracting Video URL Error , make sure you have access to linkedin learning via premium account")
        return 
    
    try:
        subtitles = data['elements'][0]['selectedVideo']['transcript']
    except :
        logging.error("Extracting Video subtitles Error")
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
    if url:
        with session.get(url, headers=HEADERS, stream=True) as r:
            try:
                if not r.headers.get('content-length','') : return
                with open(output, 'wb') as f:
                    total_length = int(r.headers.get('content-length',0))
                    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
                        if chunk:
                            f.write(chunk)
                            f.flush()
            except Exception as e:
                logging.error(f"[!] Error while downloading: '{e}'")
                if os.path.exists(output):
                    os.remove(output)
    else:
        logging.info(f'[!!] Error while Downloaind ==> Not a valid URL')
