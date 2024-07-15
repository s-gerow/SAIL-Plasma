import numpy
import requests
from bs4 import BeautifulSoup

def nav_html_dir(dir_url):
    nav = dir_url
    while input(f"Navigate to {nav}| Y or N") != "quit"or"Quit"or"N":
        if nav[-4] == '.':
            filename = ""
            for i in range(0,len(target)):
                if target[i] == '/':
                    filename = target[i+1:]
            response = requests.get(nav)
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    file.write(response.content)
                print(f"File contents at {nav} succesfully downloaded to file {filename}")
            else:
                print(f"Failed to Download File. Status code: {response.status_code}")
            return filename
        response = requests.get(nav)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)]
            links[0] = "Quit"
            for link in enumerate(links):
                print('| {:2} | {:<75} |'.format(*link))
            input_ = int(input("Navigate to:"))
            if input_ == 0:
                print("Left Directory")
                return
            else:
                target = links[input_]
                for i in range(0,len(nav)):
                    if dir_url[-i:] == target[:i]:
                        nav = dir_url + target[i:]
        else:
            print(f"Failed to retreive directory. Status code: {response.status_code}")
    return