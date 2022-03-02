import requests
from bs4 import BeautifulSoup
import sqlite3

base_url = 'https://ru.wikipedia.org/wiki/'
url = base_url + '%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B4%D0%B5%D0%BF%D1%83%D1%82%D0%B0%D1%82%D0%BE%D0%B2_%D0%93%D0%BE%D1%81%D1%83%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D0%BE%D0%B9_%D0%B4%D1%83%D0%BC%D1%8B_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B9%D1%81%D0%BA%D0%BE%D0%B9_%D0%A4%D0%B5%D0%B4%D0%B5%D1%80%D0%B0%D1%86%D0%B8%D0%B8_III_%D1%81%D0%BE%D0%B7%D1%8B%D0%B2%D0%B0'

main_page_html = BeautifulSoup(requests.get(url).text, features='lxml')

persons_table = main_page_html.find('table', {'class': 'wikitable sortable'}).find('tbody').find_all('tr')

con = sqlite3.connect('db')
cur = con.cursor()

for row in persons_table:
    cells = row.find_all('td')
    try:
        __name, _consignment = cells[0].find('a'), cells[3].find('a')
        _name = __name['title'].strip().split()
        name = _name[0][:-1] + ' ' + _name[1][0] + '.' + _name[2][0] + '.'
        if _consignment is not None:
            consignment = _consignment.text.strip()
        else:
            consignment = cells[3].text.strip()
        county = cells[4].text.strip()
    except IndexError:
        continue

    deputy_url = base_url[:-6] + __name['href']
    deputy_page_html = BeautifulSoup(requests.get(deputy_url).text, features='lxml')

    info_table = deputy_page_html.find('table', {'class': 'infobox'}).find('tbody')
    place_of_birth, birth_date, education, religion, degree = '', '', '', '', ''
    # день рождения
    try:
        birth_date = info_table.find('span', {'class': 'bday'}).text
    except AttributeError:
        pass
    # место рождения
    _place_of_birth = info_table.find('span', {'data-wikidata-property-id': 'P19'})
    if _place_of_birth is not None and place_of_birth == '':
        try:
            place_of_birth = _place_of_birth.find('a')
            sp_place_of_birth = _place_of_birth.find('span')
            if sp_place_of_birth is not None:
                place_of_birth = sp_place_of_birth.text
            else:
                if place_of_birth['title'] is None:
                    place_of_birth = _place_of_birth.text[:_place_of_birth.text.find(';')]
                else:
                    place_of_birth = place_of_birth.text
        except AttributeError and TypeError:
            place_of_birth = _place_of_birth.text[:_place_of_birth.text.find(';')]
    # образование
    _education = info_table.find_all('span', {'data-wikidata-property-id': 'P69'})
    if _education is not None and education == '':
        for __education in _education:
            try:
                education += __education.find('a').text + ';'
            except AttributeError:
                education += __education.text
    # степень
    _degree = info_table.find('span', {'data-wikidata-property-id': 'P512'})
    if _degree is not None and degree == '':
        try:
            degree = _degree.find('a').text
        except AttributeError:
            degree = _degree.text
    # обновим партию на всякий
    _consignment = info_table.find_all('span', {'data-wikidata-property-id': 'P102'})
    if _consignment is not None:
        for __consignment in _consignment:
            try:
                consignment = __consignment.find('a').text
            except AttributeError:
                pass

    _religion = info_table.find_all('span', {'data-wikidata-property-id': 'P140'})
    if _religion is not None:
        for __religion in _religion:
            try:
                religion = __religion.find('a')
                if religion is None:
                    religion = __religion.text
                else:
                    religion = religion.text
            except AttributeError and TypeError:
                religion = __religion.text

    cur.execute('''insert or replace into deputies
                    (name, cnv, consignment, county, birth_date,
                    place_of_birth, education, religion, degree)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, 3, consignment, county, birth_date, place_of_birth, education, religion, degree))
    con.commit()

    print(name, consignment, county, birth_date, place_of_birth, education, religion, degree)


con.close()
