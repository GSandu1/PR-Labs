import requests
from bs4 import BeautifulSoup

# from homework import extract_info


def recursive(maxIterations, currentIteration, URL_array, data):
    URL = URL_array[currentIteration]
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    for link in soup.find_all('a', href=True, class_='js-item-ad'):
        link = str(link.get('href'))
        if link[1] != 'b':
            url_to_append = 'https://999.md/' + link
            data.append(url_to_append)

    pages = soup.select('nav.paginator > ul > li > a')
    for page in pages:
        link = str('https://999.md' + page['href'])
        if link not in URL_array:
            URL_array.append(link)

    if currentIteration == maxIterations or currentIteration >= len(URL_array)-1:
        print(data)
        return data
    else:
        recursive(maxIterations, currentIteration+1, URL_array, data)


URL_array = ["https://999.md/ro/list/sports-health-and-beauty/pools"]
links = recursive(100000000, 0, URL_array, [])
