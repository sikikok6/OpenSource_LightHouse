import time
import requests
import pandas as pd
import threading
import git
from seleniumwire import webdriver
import schedule

# from multiprocessing.pool import Pool

global Token_List


def token_generate(bus_num, bus_dir):
    url = 'https://bis.dsat.gov.mo:37812/macauweb/routeLine.html?routeName={}&direction={}&language=zh-tw&ver=3.6.8'.format(
        bus_num, bus_dir)
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome(chrome_options=option)
    driver.get(url)
    time.sleep(5)
    for request in driver.requests:
        if request.url == "https://bis.dsat.gov.mo:37812/macauweb/routestation/bus":
            token = request.headers.get("token")
            head = token[:-12]
            tail = token[-8:]
    return head, tail


def token_list_renew(bus_list, token_list=None):
    if token_list is None:
        token_list = list("None")
    if token_list[0] == time.strftime('%D'):
        return token_list
    else:
        token_list = [time.strftime('%D')]
        token_dict = dict()
        for bus in bus_list:
            bus_num = bus[0:bus.find('-')]
            bus_dir = bus[-1]
            head, tail = token_generate(bus_num, bus_dir)
            token_dict[bus] = [head, tail]
            # token_list.append([bus, head, tail])
        token_list.append(token_dict)
        return token_list


def Main_Crawler(bus_num, bus_dir, head, tail):
    def getbusinfo(head, tail, bus_num, bus_dir):
        cookies = {}

        headers = {
            'token': head + time.strftime('%H%M') + tail,
        }

        data = {
            'action': 'dy',
            'routeName': bus_num,
            'dir': bus_dir,
            'lang': 'zh-tw',
            'device': 'web'
        }

        response = requests.post('https://bis.dsat.gov.mo:37812/macauweb/routestation/bus', headers=headers,
                                 cookies=cookies, data=data)
        return response.json()

    def generate_info(busdata):
        InfoList = []
        ######REVERSED HERE#####
        for i in reversed(range(len(busdata))):
            staInfo = busdata[i]
            staCode = staInfo['staCode']

            for j in range(len(staInfo['busInfo'])):
                busInfo = staInfo['busInfo'][j]

                busPlate = busInfo['busPlate']
                status = busInfo['status']

                dic_key = ['busPlate', 'status', 'staCode']
                dic_value = [busPlate, status, staCode]
                dic_info = dict(zip(dic_key, dic_value))
                # print(dic_info)
                InfoList.append(dic_info)
        return InfoList

    def get_traffic_info(bus_num, bus_dir):
        HUID = "a9ab7aee-087b-488e-a5f2-c0412d71799c"
        bus_num = (5 - len(bus_num)) * "0" + bus_num
        url = "https://bis.dsat.gov.mo:37812/ddbus/common/supermap/routeStation/traffic?device=web&HUID={}&routeCode={}&direction={}&indexType=00".format(
            HUID, bus_num, bus_dir)
        response = requests.get(url)
        return response.json()

    def generate_info_traffic(traffic_data):
        InfoList = []
        for item in traffic_data["data"]["stationInfo"]:
            InfoList.append([item["stationCode"], item["trafficLevel"]])
        return InfoList

    ##巴士列表中是否出现过这辆车,并根据此生成新车牌号
    def CheckAndGenBusPlate(RawBusPlate):
        if (RawBusPlate not in Bus_Dic):
            Bus_Dic[RawBusPlate] = 0

        return RawBusPlate + '-' + str(Bus_Dic[RawBusPlate])

    ##是否需要向时刻表中添加车牌作为索引
    def CheckAddTable(busPlate):
        if (busPlate not in tableInfo['Bus'].values):
            NewAdd = [busPlate]
            for _ in range(len(colName) - 1):
                NewAdd.append("")
            rowNum = tableInfo.shape[0]
            tableInfo.loc[rowNum] = NewAdd
            # AddForTrafic
            tableTraffic.loc[rowNum] = NewAdd

    def UpdateBusPlate(NewBusPlate):
        RawBusPlate = NewBusPlate[:6]
        Bus_Dic[RawBusPlate] += 1

    def Commit_Crawler_File(file_name, message):
        repo = git.Repo.init()
        repo.git.add('./csvfile'+file_name)
        repo.git.commit(m=message)
        repo.git.push()

    busdata_txt = getbusinfo(head, tail, bus_num, bus_dir)
    busdata = busdata_txt['data']['routeInfo']
    InfoList = generate_info(busdata)

    ####!!!STALIST!!!!
    staList = []
    for i in range(len(busdata)):
        staInfo = busdata[i]
        staCode = staInfo['staCode']
        staList.append(staCode)
    colName = staList.copy()
    colName.insert(0, 'Bus')
    colValue = ['' for i in range(len(colName))]
    # 列表不会吞重复值
    rowDic = dict(zip(colName, colValue))

    tableInfo = pd.DataFrame(data=None, columns=colName)
    #
    tableTraffic = pd.DataFrame(data=None, columns=colName)

    Bus_Dic = {}

    CreateTime = time.strftime('%m%d-%H%M')
    CsvName = bus_num + bus_dir + '-' + CreateTime + '.csv'
    CsvName_traffic = bus_num + bus_dir + '-' + CreateTime + '_traffic.csv'

    # MainPart
    # WORK 8H
    '''
    def init():
        return None
    def MainPart():
        return None
    '''

    for _ in range(70):
        # EVERY 10MINUTE
        for _ in range(60):
            try:
                busdata_txt = getbusinfo(head, tail, bus_num, bus_dir)
                traffic_data_txt = get_traffic_info(bus_num, bus_dir)
            except:
                print(bus_num + '-' + bus_dir + "Failed on renewing at " + time.strftime('%H:%M'))
            else:
                busdata = busdata_txt['data']['routeInfo']
                InfoList = generate_info(busdata)

                InfoList_traffic = generate_info_traffic(traffic_data_txt)

                index_info = 0
                index_end = len(colName) - 1
                index_col = index_end
                time_str = time.strftime('%H%M%S')
                while index_info < len(InfoList) and index_col > 0:

                    if InfoList[index_info]['staCode'] != colName[index_col]:
                        index_col -= 1
                        continue

                    elif InfoList[index_info]['status'] == 0:
                        index_info += 1
                        continue

                    else:
                        RawBusPlate = InfoList[index_info]['busPlate']
                        NewBusPlate = CheckAndGenBusPlate(RawBusPlate)

                        ##到达终点站情形，避开特殊节点爬，默认已有前表
                        if index_col == index_end:
                            if NewBusPlate not in tableInfo['Bus'].values:
                                index_info += 1
                                continue
                            UpdateBusPlate(NewBusPlate)

                        CheckAddTable(NewBusPlate)
                        index_row = tableInfo[tableInfo.Bus == NewBusPlate].index.tolist()[0]
                        ##已有值则不添加
                        if tableInfo.iloc[index_row, index_col] == "":
                            tableInfo.iloc[index_row, index_col] = time_str
                            tableTraffic.iloc[index_row, index_col] = InfoList_traffic[index_col - 1][1]
                        index_info += 1

            time.sleep(10)
        ##WriteToCSV
        tableInfo.to_csv('./csvfile/' + CsvName)
        tableTraffic.to_csv('./csvfile/' + CsvName_traffic)
        print(bus_num + '-' + bus_dir + " Write to Table at " + time.strftime('%H:%M'))
        ##CommitToGitHub
        # try:
        #     Message = "Commit Csv At " + time.strftime('%H%M')
        #     Commit_Crawler_File(CsvName, Message)
        #     Commit_Crawler_File(CsvName_traffic, Message)
        #
        #     print(f"{CsvName}:{Message}")
        # except:
        #     print(f"Failed commit {CsvName}")


def thread(bus_num, bus_dir, head, tail):
    thr = threading.Thread(name=bus_num + "-" + bus_dir, target=Main_Crawler, args=(bus_num, bus_dir, head, tail))
    thr.start()


def main():
    #Bus_List = ['51-0', ]
    Bus_List = ['25-0', '25-1',
                 '26-0', '26-1',
                 '26A-0', '26A-1',
                 '51A-0', '51A-1']
    Token_List = token_list_renew(Bus_List)
    print("FinishedGenerateToken")

    for (key, value) in Token_List[1].items():
        bus_num = key[0:key.find('-')]
        bus_dir = key[-1]
        head = value[0]
        tail = value[1]
        thread(bus_num, bus_dir, head, tail)


main()
'''
schedule.every().day.at("07:00").do(main)
while True:
    schedule.run_pending()
    '''

