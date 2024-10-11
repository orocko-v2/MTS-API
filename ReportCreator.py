import datetime
import os, re, pandas as pd
import time
import requests.exceptions

import Authentication
import Requests
import config_path_file

reportDone = False
def findPhoneNumbersFile():
    """
    find file with phone numbers by regex
    :return: filename
    """
    datapath = config_path_file.DATA_PATH

    filename_regex = re.compile('bill_phone_numbers_' + '\d\d_\d\d_20\d\d' + '\.xls')

    for root, dirs, files in os.walk(datapath):
        for file in files:
            if filename_regex.match(file):
                return file

def createDailyReport(file, nds, report_date=None):
    """
    create report with phone number and day outcome and save it into Excel file
    :return: dataframe with data
    """
    global reportDone
    if file is None:
        return
    print(file)
    df = pd.read_excel(file)
    list = []
    print('start creating report')
    print('reportDone=', reportDone)
    phones = df.get('Абонентский номер')
    print(phones)
    if reportDone:
        return
    if report_date == None:
        report_date = datetime.datetime.now()
    for phone in phones:
        i = 0
        successful = False
        while not successful:
            print(successful)
            try:

                createdRequestDailyExpenses = Requests.createRequest(flag='BILLS_BY_MSISDN',
                                                                     params_list=[phone, report_date - datetime.timedelta(1), report_date])

                next_month = report_date.replace(day=28) + datetime.timedelta(days=4)
                createdRequestMonthlyExpenses = Requests.createRequest(flag='BILLS_BY_MSISDN',
                                                                       params_list=[phone, report_date.replace(day=1), report_date])
                print('STATUS_CODES', createdRequestDailyExpenses.status_code, createdRequestMonthlyExpenses.status_code)
                if createdRequestDailyExpenses.status_code == requests.codes.ok and createdRequestMonthlyExpenses.status_code == requests.codes.ok:
                    successful = True
                    month_amount = summarize(createdRequestMonthlyExpenses)
                    amount = summarize(createdRequestDailyExpenses)
                    index = int(df[df['Абонентский номер']==phone].index.values.astype(int)[0])
                    name = df.get('ФИО')[index]
                    commentary = df.get('Комментарий')[index]
                    limit = df.get('Лимит')[index]
                    limit_excess = month_amount - limit
                    if limit_excess < 0:
                        limit_excess = 0
                    nds_percentage = (1-nds/100)
                    no_nds_value = amount* nds_percentage
                    no_nds_month_value = month_amount * nds_percentage
                    data = [phone, name, commentary, amount, no_nds_value, month_amount, no_nds_month_value, limit_excess]
                    print(data)
                    list.append(data)
                else:
                    time.sleep(10)
            except requests.exceptions.HTTPError as e:
                print(e.args)
                if (int(e.args[0][0:3]) == 429):
                    print('sleep')
                    time.sleep(10)
                    continue
                elif (int(e.args[0][0:3]) == 401) and i < 3:
                    Authentication.LoginUser(Authentication._login, Authentication._password)
                    time.sleep(60)
                    i+=1
                    continue
                else:
                    print('wtf')
                    successful = True
                    continue
    path = uniquify('reports/otchet/report_' + report_date.date().strftime("%d_%m_%y") + '.xlsx')
    new_df = pd.DataFrame(list, columns = ['Абонентский номер', 'ФИО', 'Комментарий', 'Расходы за день с НДС', 'Расходы за день без НДС','Расходы с начала месяца с НДС',  "Расходы с начала месяца без НДС",  'Превышение лимита'])
    if not new_df.empty:
        writer = pd.ExcelWriter(path)
        print(new_df.dtypes)
        print(new_df)
        new_df.to_excel(writer,sheet_name='Sheet1', index=False)
        for column in new_df:
            print(column)
            column_width = max(new_df[column].astype(str).map(len).max() + 1, len(column) + 1)
            col_idx = new_df.columns.get_loc(column)
            writer.sheets['Sheet1'].set_column(col_idx, col_idx, column_width)
        writer.close()
    print('done')
    reportDone = True
    return new_df

def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1
    return path

def summarize(rqst):
    sum = 0
    for oper in rqst.json()['Usages']:
        if oper['type'] != 'income':
            sum += oper['amount']
    return sum



