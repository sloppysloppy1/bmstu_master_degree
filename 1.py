import requests
from bs4 import BeautifulSoup
import sqlite3

base_url = 'https://sozd.duma.gov.ru'
base_search_url = base_url + '/oz?b%5BNumberSpec%5D=&b%5BAnnotation%5D=&b%5BIsArchive%5D%5B0%5D=cnv-{0}&b%5BYear%5D=&b%5BFzNumber%5D=&b%5BNameComment%5D=&b%5BResolutionnumber%5D=&b%5BfirstCommitteeCond%5D=and&b%5BsecondCommitteeCond%5D=and&b%5BExistsEventsDate%5D=&b%5BMaxDate%5D=&b%5BDecisionsDateOfCreate%5D=&b%5BconclusionRG%5D=&b%5BdateEndConclusionRG%5D=&b%5BResponseDate%5D=&b%5BAmendmentsDate%5D=&b%5BSectorOfLaw%5D=&b%5BClassOfTheObjectLawmakingId%5D=34f6ae40-bdf0-408a-a56e-e48511c6b618&date_period_from_Year=&date_period_to_Year=&cond%5BClassOfTheObjectLawmaking%5D=any&cond%5BThematicBlockOfBills%5D=any&cond%5BPersonDeputy%5D=any&cond%5BFraction%5D=any&cond%5BRelevantCommittee%5D=any&cond%5BResponsibleCommittee%5D=any&cond%5BHelperCommittee%5D=any&cond%5BExistsEvents%5D=any&cond%5BLastEvent%5D=any&cond%5BExistsDecisions%5D=any&cond%5BLastDecisions%5D=any&cond%5BQuestionOfReference%5D=any&cond%5BSubjectOfReference%5D=any&cond%5BFormOfTheObjectLawmaking%5D=any&cond%5BinSz%5D=any&date_period_from_ExistsEventsDate=&date_period_to_ExistsEventsDate=&date_period_from_MaxDate=&date_period_to_MaxDate=&date_period_from_DecisionsDateOfCreate=&date_period_to_DecisionsDateOfCreate=&date_period_from_dateEndConclusionRG=&date_period_to_dateEndConclusionRG=&date_period_from_ResponseDate=&date_period_to_ResponseDate=&date_period_from_AmendmentsDate=&date_period_to_AmendmentsDate=&page_34F6AE40-BDF0-408A-A56E-E48511C6B618={1}#data_source_tab_b'

def get_elems_from_page(html_text, params, flg = 0):
    if flg == 0:
        elems = html_text.find_all(*params)
    else:
        elems = html_text.find(*params)
    return elems

f = open('denied.txt', 'a')
snv, pages = map(int, input().split())

for page in range(1, pages + 1):
    # cnv - законопроект
    url = base_search_url.format(snv, page)
    # получаем все законопроекты со страницы
    search_page_html = BeautifulSoup(requests.get(url).text, features='lxml')
    bills = get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open first_item'})) \
            + get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open'})) \
            + get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open last_item'}))
    for bill in bills:
        print('качаем 1 закон')
        bill_urn = bill.get('data-clickopen')
        bill_url = base_url + bill_urn
        # номер закона
        bill_num = bill_urn[bill_urn.rfind('/')+1:len(bill_urn)]
        # получаем статус закона
        bill_page_html = BeautifulSoup(requests.get(bill_url).text, features='lxml')
        states = get_elems_from_page(bill_page_html, ('a', {'class': 'ar_rask'}))
        for state in states:
            _decision = state.get('data-original-title')
            if _decision.lower() == 'опубликование закона':
                decision = 'accepted'
                break
            elif _decision.lower() == 'отклонение законопроекта':
                decision = 'declined'
                break
        if decision == 'accepted':
            events_link = bill_url + '#bh_hron'
            events_page_html = BeautifulSoup(requests.get(events_link).text, features='lxml')
            events_table = get_elems_from_page(events_page_html, ('div', {'class': 'bhr_item'}))[0]
            events = events_table.find_all('div', {'class': 'ch-item'})
            for _event in events:
                event = _event.find('div', {'class': 'ch-item-header'}).text.strip().lower()
                if event.find('откл') != -1:
                    f.write(event + str(bill_num) + ' \n')
                    break
                elif event.find('отоз') != -1 or event.find('отзы') != -1:
                    f.write(event + str(bill_num) + ' \n')
                    break
