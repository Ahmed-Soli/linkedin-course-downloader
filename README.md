# linkedin-course-downloader
python script for downloading courses from linkedin learning with subtitles


# Based on liranbg's linkedin-learning-downloader But got restructured 

Dependencies:

Python 3
requests
lxml
clint
pickle

Please use this script for your own purposes.

This script was written for educational usage and personal use only.

Make sure your LinkedIn account is NOT protected with 2FA

# Installing dependencies:

`pip install -r requirements.txt`
# To add you info Use 
`python required_info.py`
Then fillin your info and click save 

# Or you can Open required_info.json put your  (linkedin email, password, and courses slugs or courses links)

it will be like this
`{
    "linkedin_email": "",
    "linkedin_password": "",
    "courses_links":
    ["https://www.linkedin.com/learning/learning-c-5", "learning-c-5"]
}`

e.g:
COURSE URL: https://www.linkedin.com/learning/python-advanced-design-pattern
->
SLUG: python-advanced-design-pattern

# Usage
`python required_info.py`
`python downloader.py`

# Re-structued by Ahmed Soliman

![Screen Shot of the Gui for the required info 1](images/required_info.PNG)
![Test Image 2](images/linkedin_downloader.gif)

![Test Image 3](images/proof1.PNG)

![Test Image 4](images/proof2.PNG)
