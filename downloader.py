


from Loging_in import login
import logging
from config import USERNAME, PASSWORD
from fetch_info import fetch_courses





def process():
    try:
        logging.info("[*] -------------Login-------------")
        session               =  login(USERNAME, PASSWORD)
        
        logging.info("[*] -------------Done-------------")

        logging.info("[*] -------------Fetching Course-------------")
        fetch_courses(session)
        logging.info("[*] -------------Done-------------")

    except Exception as e:
        logging.error(f"Connection Error: {e}")


if __name__ == "__main__":
    process()
