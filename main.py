import requests
from bs4 import BeautifulSoup
import sqlite3

base_url = 'https://sozd.duma.gov.ru'
base_search_url = base_url + '/oz?b%5BNumberSpec%5D=&b%5BAnnotation%5D=&b%5BIsArchive%5D%5B0%5D=cnv-{0}&b%5BYear%5D=&b%5BFzNumber%5D=&b%5BNameComment%5D=&b%5BResolutionnumber%5D=&b%5BfirstCommitteeCond%5D=and&b%5BsecondCommitteeCond%5D=and&b%5BExistsEventsDate%5D=&b%5BMaxDate%5D=&b%5BDecisionsDateOfCreate%5D=&b%5BconclusionRG%5D=&b%5BdateEndConclusionRG%5D=&b%5BResponseDate%5D=&b%5BAmendmentsDate%5D=&b%5BSectorOfLaw%5D=&b%5BClassOfTheObjectLawmakingId%5D=34f6ae40-bdf0-408a-a56e-e48511c6b618&date_period_from_Year=&date_period_to_Year=&cond%5BClassOfTheObjectLawmaking%5D=any&cond%5BThematicBlockOfBills%5D=any&cond%5BPersonDeputy%5D=any&cond%5BFraction%5D=any&cond%5BRelevantCommittee%5D=any&cond%5BResponsibleCommittee%5D=any&cond%5BHelperCommittee%5D=any&cond%5BExistsEvents%5D=any&cond%5BLastEvent%5D=any&cond%5BExistsDecisions%5D=any&cond%5BLastDecisions%5D=any&cond%5BQuestionOfReference%5D=any&cond%5BSubjectOfReference%5D=any&cond%5BFormOfTheObjectLawmaking%5D=any&cond%5BinSz%5D=any&date_period_from_ExistsEventsDate=&date_period_to_ExistsEventsDate=&date_period_from_MaxDate=&date_period_to_MaxDate=&date_period_from_DecisionsDateOfCreate=&date_period_to_DecisionsDateOfCreate=&date_period_from_dateEndConclusionRG=&date_period_to_dateEndConclusionRG=&date_period_from_ResponseDate=&date_period_to_ResponseDate=&date_period_from_AmendmentsDate=&date_period_to_AmendmentsDate=&page_34F6AE40-BDF0-408A-A56E-E48511C6B618={1}#data_source_tab_b'

# созыв -> количество страниц
cnv_pages = [[3, 481], [8, 35], [7, 651], [6, 639], [5, 471], [4, 483]]

# получаем элементы со страницы
def get_elems_from_page(html_text, params, flg = 0):
    if flg == 0:
        elems = html_text.find_all(*params)
    else:
        elems = html_text.find(*params)
    return elems

# получаем ссылки на законопроекты
def get_bills(cnv, page_amount):
    for page in range(1, page_amount + 1):
        # cnv - законопроект
        url = base_search_url.format(cnv, page)
        # получаем все законопроекты со страницы
        search_page_html = BeautifulSoup(requests.get(url).text, features='lxml')
        bills = get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open first_item'})) \
                + get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open'})) \
                + get_elems_from_page(search_page_html, ('div', {'class': 'obj_item click_open last_item'}))
        for bill in bills:
            bill_urn = bill.get('data-clickopen')
            bill_url = base_url + bill_urn
            # номер закона
            bill_num = bill_urn[bill_urn.rfind('/')+1:len(bill_urn)]
            # страница с законом
            bill_page_html = BeautifulSoup(requests.get(bill_url).text, features='lxml')
            #states = get_elems_from_page(bill_page_html, ('a', {'class': 'ar_rask'}))
            #for state in states:
            #    _decision = state.get('data-original-title')
            #    if _decision.lower() == 'опубликование закона':
            #        decision = 'accepted'
            #        break
            #    elif _decision.lower() == 'отклонение законопроекта':
            #        decision = 'declined'
            #        break
            # получаем метадату:
            metadata_table = get_elems_from_page(bill_page_html, ('table', {'class': 'table table-hover table-striped borderless fs13px'}))[0]
            metadata = metadata_table.find_all('tr')
            subject, bill_type, committee, field, theme_block = '', '', '', '', ''
            for _metadata in metadata:
                item = _metadata.find('span', {'class': 'opch_l_txt'}).text.lower()
                value = _metadata.find('div', {'class': 'opch_r'}).text.strip()
                if item.find('субъект') != -1:
                    subject = value
                elif item.find('форма законопроекта') != -1:
                    bill_type = value
                elif item.find('комитет') != -1:
                    if committee.find(value.strip()) == -1:
                        committee += value + ';'
                elif item.find('отрасль') != -1:
                    field = value
                elif item.find('тематический блок') != -1:
                    theme_block = value
            # получаем даты:
            events_link = bill_url + '#bh_hron'
            events_page_html = BeautifulSoup(requests.get(events_link).text, features='lxml')
            events_table = get_elems_from_page(events_page_html, ('div', {'class': 'bhr_item'}))[0]
            events = events_table.find_all('div', {'class': 'ch-item'})
            # последовательность событий и дат
            events_sequence, events_sequence_list, iter_dates = '', [], [''] * 8
            for _event in events:
                event = _event.find('div', {'class': 'ch-item-header'}).text.strip()
                date = _event.find('span', {'class': 'hron_date'}).text.strip()
                # последовательность событий
                event_num = event[0:3]
                events_sequence += event[0:3] + ';'
                events_sequence_list.append([event_num, event])
                # дата
                if event_num[0] == '1':
                    iter_dates[0] += date + ';'
                elif event_num[0] == '2':
                    iter_dates[1] += date + ';'
                elif event_num[0] == '3':
                    iter_dates[2] += date + ';'
                elif event_num[0] == '4':
                    iter_dates[3] += date + ';'
                elif event_num[0] == '5':
                    iter_dates[4] += date + ';'
                elif event_num[0] == '6':
                    iter_dates[5] += date + ';'
                elif event_num[0] == '7':
                    iter_dates[6] += date + ';'
                elif event_num[0] == '8':
                    iter_dates[7] += date + ';'

            # получаем решение по закону
            decision = 'declined'
            for state in events_sequence_list:
                if state[1].lower().find('опублик') != -1:
                    decision = 'accepted'
                    print(decision)
                    break

            denied_on_stages = ''
            for i in range(len(events_sequence_list) - 1):
                try:
                    if float(events_sequence_list[i+1][0]) < float(events_sequence_list[i][0]):
                        if events_sequence_list[i][0].find('отклон') != -1:
                            denied_stages += events_sequence_list[i]
                except TypeError:
                    pass
            print(denied_on_stages)
            # получаем все файлы
            bill_files = get_elems_from_page(bill_page_html, ('a', {'class': 'a_event_files'}))
            extra_file_url, extra_file_extension = '', ''
            for file in bill_files:
                # проверяем, что это текст закона
                filenames = file.find_all('div', {'class': 'doc_wrap'})
                for filename in filenames:
                    _filename = filename.text.lower()
                    if _filename.find('текст') != -1 and _filename.find('закон') != -1:
                        file_url = base_url + file.get('href')
                        # получаем расширение файла
                        _filename_header = requests.get(file_url).headers.get('content-disposition', '')
                        if _filename_header.rfind('.') != -1:
                            file_extension = _filename_header[_filename_header.rfind('.')+1:len(_filename_header)]
                        else:
                            file_extension = 'html'
                        __filename = _filename
                    elif _filename.find('поясн') != -1 and _filename.find('записка') != -1:
                        extra_file_url = base_url + file.get('href')
                        _filename_header = requests.get(extra_file_url).headers.get('content-disposition', '')
                        if _filename_header.rfind('.') != -1:
                            extra_file_extension = _filename_header[_filename_header.rfind('.')+1:len(_filename_header)]
                        else:
                            extra_file_extension = 'html'
                        ___filename = _filename
            # суем в бд
            cur.execute('''insert or replace into bills
                            (bill_num, cnv, subject, bill_type, committee, field,
                            theme_block, decision, file_url, file_extension,
                            extra_file_url, extra_file_extension, events_sequence,
                            date1, date2, date3, date4, date5, date6, date7, date8)
                        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (bill_num, cnv, subject, bill_type, committee, field, theme_block, decision, file_url,
                            file_extension, extra_file_url, extra_file_extension, events_sequence,
                            iter_dates[0], iter_dates[1], iter_dates[2], iter_dates[3], iter_dates[4],
                            iter_dates[5], iter_dates[6], iter_dates[7]))
            con.commit()
            print ('текущий: ',[__filename, ___filename, cnv, subject, bill_type,
                committee, field, theme_block, bill_num, decision, file_url, file_extension,
                extra_file_url, extra_file_extension, events_sequence,
                iter_dates[0], iter_dates[1], iter_dates[2], iter_dates[3], iter_dates[4],
                iter_dates[5], iter_dates[6], iter_dates[7]])

# запуск
if __name__ == '__main__':
    # подключение к бд
    con = sqlite3.connect('db')
    cur = con.cursor()
    # выбор собрания
    convocation = int(input('введите созыв: '))
    # запуск
    for elem in cnv_pages:
        if elem[0] == convocation:
            get_bills(*elem)
    con.close()
