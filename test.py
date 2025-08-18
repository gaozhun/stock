import akshare as ak

fund_name_em_df = ak.fund_name_em()
print(fund_name_em_df)

fund_name_em_df.to_csv('fund_name_em.csv', index=False)

基金代码,拼音缩写,基金简称,基金类型,拼音全称
000001,HXCZHH,华夏成长混合,混合型-灵活,HUAXIACHENGZHANGHUNHE
