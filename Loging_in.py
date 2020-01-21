import logging
import requests
import lxml.html
from urllib.parse import urljoin

def login(username, password,req_session=requests.Session(),URL='https://www.linkedin.com/login/'):
    with req_session as session:
        logging.info("[*] Login step 1 - Getting CSRF token...")
        resp = session.get(URL,headers={'user-agent': 'Mozilla/5.0'})
        body = resp.text

        # Looking for CSRF Token
        html            = lxml.html.fromstring(body)
        csrf            = html.xpath("//input[@name='loginCsrfParam']/@value").pop()
        sIdString       = html.xpath("//input[@name='sIdString']/@value").pop()
        parentPageKey   = html.xpath("//input[@name='parentPageKey']/@value").pop()
        pageInstance    = html.xpath("//input[@name='pageInstance']/@value").pop()
        loginCsrfParam  = html.xpath("//input[@name='loginCsrfParam']/@value").pop()
        fp_data         = html.xpath("//input[@name='fp_data']/@value").pop()
        d               = html.xpath("//input[@name='_d']/@value").pop()
        controlId       = html.xpath("//input[@name='controlId']/@value").pop()
        # logging.debug(f"[*] CSRF: {csrf}")
        data = {
            "session_key": username,
            "session_password": password,
            "csrfToken": csrf,
            'ac': 0,
            'sIdString': sIdString,
            'parentPageKey':parentPageKey,
            'pageInstance': pageInstance,
            'trk': '',
            'authUUID': '',
            'session_redirect': '',
            'loginCsrfParam': loginCsrfParam,
            'fp_data': fp_data,
            '_d': d,
            'controlId': controlId
        }
        
        logging.info("[*] Login step 1 - Done")
        logging.info("[*] Login step 2 - Logging In...")
        URL = urljoin('https://www.linkedin.com', 'checkpoint/lg/login-submit')
        session.post(URL, data=data,headers={'user-agent': 'Mozilla/5.0'})
            
        if not session.cookies._cookies['.www.linkedin.com']['/'].get('li_at',''):
            raise RuntimeError("[!] Could not login. Please check your credentials")
        
        logging.info("[*] Login step 2 - Done")
        return session

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)