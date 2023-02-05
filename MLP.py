from sklearn.neural_network import MLPRegressor
from sklearn.datasets import make_regression



import pandas as pd

file_path ="/Users/zhouyinuo/PycharmProjects/crawler/VersionUpdate/Train.csv"
df = pd.read_csv(file_path,index_col=0)

train = df[df.columns[0:-2]]
X_Train = train.to_numpy()

train = df[df.columns[-1]]
Y_Train = train.to_numpy()

regr = MLPRegressor(random_state=1, max_iter=500).fit(X_Train, Y_Train)


file_path ="/Users/zhouyinuo/PycharmProjects/crawler/VersionUpdate/Test.csv"
df = pd.read_csv(file_path,index_col=0)

test = df[df.columns[0:-2]]
X_Test = test.to_numpy()

train = df[df.columns[-1]]
Y_Test = train.to_numpy()

#X_Test =[[50678,3,6]] #50748 50731
Y_Predict = regr.predict(X_Test)

print(Y_Predict)

ans = regr.score(X_Test, Y_Test)
print(ans)



