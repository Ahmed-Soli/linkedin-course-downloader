import logging , requests , lxml.html , os
from urllib.parse import urljoin
import pickle

def save_cookies(session,filename):
    with open(filename, 'wb') as f:
        pickle.dump(session.cookies, f)
    

def load_cookies(session,filename):
    with open(filename,'rb') as f:
        session.cookies.update(pickle.load(f))

def login(username, password,session=requests.Session()):
    
    home_url='https://www.linkedin.com/'
    if os.path.exists(filename):
        logging.info("[*] Login step 0 - Loading Cookies...")
        load_cookies(session,filename)
        res = session.get(home_url, headers={'User-Agent': 'Mozilla/5.0'})
        if not '>Sign in</' in res.text :
            logging.info('[*] Login success')
            return True
    logging.info("[*] Login step 1 - Getting CSRF token...")
    resp = session.get(urljoin(home_url,'/login/'),headers={'user-agent': 'Mozilla/5.0'})
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
    logging.debug(f"[*] CSRF: {csrf}")
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
        logging.info("[!] Could not login. Please check your credentials")
        return False
    logging.info("[*] Login step 2 - Done")
    
    logging.info("[*] Login step 3 - Saving Cookies...")
    save_cookies(session,filename)
    return True

filename   = 'cookie_linkedin.txt'
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)