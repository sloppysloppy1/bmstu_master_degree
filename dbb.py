import sqlite3
con = sqlite3.connect('db')
cur = con.cursor()

def tab_bills():
    cur.execute('drop table bills')
    cur.execute('''create table bills (
                    id integer primary key,
                    bill_num text not null unique,
                    cnv tinyint not null,
                    subject text,
                    bill_type text,
                    committee text,
                    field text,
                    theme_block text,
                    decision text not null,
                    file_url text not null,
                    file_extension text not null,
                    extra_file_url text,
                    extra_file_extension text,
                    events_sequence text not null,
                    date1 text,
                    date2 text,
                    date3 text,
                    date4 text,
                    date5 text,
                    date6 text,
                    date7 text,
                    date8 text,
                    dl_flg varchar(1),
                    upd_flg varchar(1));''')
    con.commit()

def tab_deps():
    cur.execute('drop table deputies')
    cur.execute('''create table deputies (
                    id integer primary key,
                    name text not null unique,
                    gender text,
                    cnv tinyint not null,
                    consignment text,
                    county text,
                    birth_date text unique,
                    place_of_birth text,
                    education text,
                    degree text,
                    religion text );''')
    con.commit()

def alter_bills():
    #cur.execute('alter table bills add column dl_flg varchar(1) default 0')
    cur.execute('alter table bills add column upd_flg varchar(1) default 0')
alter_bills()

con.close()
