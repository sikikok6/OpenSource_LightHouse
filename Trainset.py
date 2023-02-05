import os
import pandas as pd

def int_to_sec(var_time):
    hour = round(var_time / 10000, 0)
    minute = round(var_time / 100, 0) % 100
    second = var_time % 100

    # print(f"{hour},{minute},{second}")
    return 3600 * hour + 60 * minute + second


work_dir = "/Users/zhouyinuo/PycharmProjects/crawler/VersionUpdate/Test"
dirs = os.listdir(work_dir)
# Deal With Mac OS has '.DS_Store'
dirs = [f for f in dirs if not f.startswith('.DS_Store')]
dirs.sort()


total_list = []

week = 7
for dir in dirs:
    week = week%7

    print(dir)
    # xxxx/Clean/01xx/
    read_path = os.path.join(os.getcwd(), 'Test', dir)

    busfile = '26A0' + '-' + dir + '.csv'
    file_path1 = os.path.join(read_path, busfile)

    trafficfile = '26A0' + '-' + dir + '-Traffic.csv'
    file_path2 = os.path.join(read_path, trafficfile)

    df1 = pd.read_csv(file_path1, index_col=0)
    df1 = df1[df1.columns[1:-1]].apply(int_to_sec)

    df2 = pd.read_csv(file_path2, index_col=0)
    df2 = df2[df1.columns[0:-1]]

    #每行
    for indexs in df1.index:
        temp1 = df1.loc[indexs].values
        temp2 = df2.loc[indexs].values
        for i in range(len(temp1) - 1):
            temp_list = []
            temp_list.append(int(temp1[i]))  # Time
            temp_list.append(temp2[i])  # Traffic
            temp_list.append(i)  # Id
            temp_list.append(week) #WEEK
            temp_list.append(int(temp1[i + 1]))  # Label
            total_list.append(temp_list)

    week += 1

data = pd.DataFrame(total_list)
data.to_csv('./Test.csv')

