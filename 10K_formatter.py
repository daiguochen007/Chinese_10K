# -*- coding: UTF-8 -*-
"""
Created on Tue Jul 24 20:00:41 2018

@author: Dai
"""
import csv
import urllib2
import pandas as pd

def get_10K_raw(seccode):
    """
    从网易财经抓取财报历史数据
    seccode = "000002" 万科
    """
    res = {}
    for tbl in ["zcfzb","lrb","xjllb"]:
        url = "http://quotes.money.163.com/service/"+tbl+"_"+seccode+".html"
        response = urllib2.urlopen(url)
        cr = csv.reader(response)
        df = {}
        i=0
        for row in cr:
            df[i]=row
            i+=1
        del df[i-1]
        
        df=pd.DataFrame(df).T
        # convert to chinese
        for c in df.columns:
            df[c] = map(lambda x:x.decode('gb2312').encode('utf-8').strip(),df[c])
        df.columns = df.iloc[0,:]
        df = df.iloc[1:,:-1]
        df.index = range(len(df))
        #replace --
        df = df.replace("--",0)
        for c in list(df.columns)[1:]:
            df[c] = map(lambda x:float(x) if x==x else x,df[c])
        res[tbl]=df
        print "get ["+seccode+"_"+tbl+"] finished!"
    return res


def format_zcfzb(df):
    """
    format zcfzb
    """
    tenK_structure={"asset":{"liquid asset":[0,list(df["报告日期"]).index("流动资产合计(万元)")],
                             "illiquid asset":[list(df["报告日期"]).index("流动资产合计(万元)")+1,list(df["报告日期"]).index("非流动资产合计(万元)")]},
                    "liability":{"liquid liability":[list(df["报告日期"]).index("资产总计(万元)")+1,list(df["报告日期"]).index("流动负债合计(万元)")],
                                 "illiquid liability":[list(df["报告日期"]).index("流动负债合计(万元)")+1,list(df["报告日期"]).index("非流动负债合计(万元)")]},
                    "equity":{"parent equity":[list(df["报告日期"]).index("负债合计(万元)")+1,list(df["报告日期"]).index("归属于母公司股东权益合计(万元)")],
                              "minor equity":[list(df["报告日期"]).index("归属于母公司股东权益合计(万元)")+1,list(df["报告日期"]).index("少数股东权益(万元)")]}}
    liq_ass = df.iloc[tenK_structure["asset"]["liquid asset"][0]:(tenK_structure["asset"]["liquid asset"][1]+1),:].copy()
    illiq_ass = df.iloc[tenK_structure["asset"]["illiquid asset"][0]:(tenK_structure["asset"]["illiquid asset"][1]+1),:].copy()
    sum_ass = df.iloc[list(df["报告日期"]).index("资产总计(万元)"):list(df["报告日期"]).index("资产总计(万元)")+1,:].copy()
    
    liq_lia = df.iloc[tenK_structure["liability"]["liquid liability"][0]:(tenK_structure["liability"]["liquid liability"][1]+1),:].copy()
    illiq_lia = df.iloc[tenK_structure["liability"]["illiquid liability"][0]:(tenK_structure["liability"]["illiquid liability"][1]+1),:].copy()
    sum_lia = df.iloc[list(df["报告日期"]).index("负债合计(万元)"):list(df["报告日期"]).index("负债合计(万元)")+1,:].copy()
    
    par_equ = df.iloc[tenK_structure["equity"]["parent equity"][0]:(tenK_structure["equity"]["parent equity"][1]+1),:].copy()
    min_equ = df.iloc[tenK_structure["equity"]["minor equity"][0]:(tenK_structure["equity"]["minor equity"][1]+1),:].copy()
    sum_equ = df.iloc[list(df["报告日期"]).index("所有者权益(或股东权益)合计(万元)"):list(df["报告日期"]).index("所有者权益(或股东权益)合计(万元)")+1,:].copy()
    
    sum_lia_equ = df.iloc[list(df["报告日期"]).index("负债和所有者权益(或股东权益)总计(万元)"):list(df["报告日期"]).index("负债和所有者权益(或股东权益)总计(万元)")+1,:].copy()
    
    for temp in [liq_ass,illiq_ass,liq_lia,illiq_lia,par_equ,min_equ]:
        temp["报告日期"] = map(lambda x:" "*8+x,temp["报告日期"])
    
    def rowdf(mystr):
        return pd.DataFrame([mystr]+[float("nan")]*(len(df.columns)-1),index=df.columns,columns=[0]).T
    
    zcfzb = pd.concat([rowdf("资产"),rowdf("    流动资产"),liq_ass,rowdf("    非流动资产"),illiq_ass,sum_ass,
                       rowdf("负债"),rowdf("    流动负债"),liq_lia,rowdf("    非流动负债"),illiq_lia,sum_lia,
                       rowdf("股东权益"),rowdf("    母公司权益"),par_equ,rowdf("    少数股东权益"),min_equ,sum_equ,sum_lia_equ],axis=0)
    zcfzb.index= range(len(zcfzb))
    return zcfzb
    

def format_lrb(df):
    """
    format lrb
    """
    tenK_structure={"minus":[list(df["报告日期"]).index("营业总成本(万元)"),list(df["报告日期"]).index("资产减值损失(万元)")],
                    "EPS":list(df["报告日期"]).index("基本每股收益")}

    def rowdf(mystr):
        return pd.DataFrame([mystr]+[float("nan")]*(len(df.columns)-1),index=df.columns,columns=[0]).T
    
    lrb = pd.concat([df.iloc[:tenK_structure["minus"][0],:],rowdf("减："), df.iloc[tenK_structure["minus"][0]:tenK_structure["minus"][1]+1,:],rowdf("加："),
                       df.iloc[tenK_structure["minus"][1]+1:tenK_structure["EPS"],:],rowdf("每股收益"),df.iloc[tenK_structure["EPS"]:]],axis=0)
    lrb.index = range(len(lrb))
    
    #spacing
    def spacing(start_str,end_str):
        temp = [list(lrb["报告日期"]).index(start_str),list(lrb["报告日期"]).index(end_str)]
        lrb.iloc[temp[0]:temp[1]+1,0] = map(lambda x:" "*4+x,lrb.iloc[temp[0]:temp[1]+1,0])
    
    spacing("营业收入(万元)","其他业务收入(万元)")
    spacing("营业总成本(万元)","资产减值损失(万元)")
    spacing(" "*4+"营业成本(万元)"," "*4+"其他业务成本(万元)")
    spacing("营业外收入(万元)","非流动资产处置损失(万元)")
    spacing("所得税费用(万元)","未确认投资损失(万元)")
    
    temp = [list(lrb["报告日期"]).index("净利润(万元)")+1,list(lrb["报告日期"]).index("每股收益")-1]
    lrb.iloc[temp[0]:temp[1]+1,0] = map(lambda x:" "*4+x,lrb.iloc[temp[0]:temp[1]+1,0])
    lrb.iloc[list(lrb["报告日期"]).index("基本每股收益"):,0] = map(lambda x:" "*4+x,lrb.iloc[list(lrb["报告日期"]).index("基本每股收益"):,0])
    return lrb


def format_xjllb(df):
    """
    format xjllb
    """
    df.columns= map(lambda x:x.strip(),df.columns)
    df["报告日期"] = map(lambda x:x.strip(),df["报告日期"])
    tenK_structure={"cf operating":[0,list(df["报告日期"]).index("经营活动产生的现金流量净额(万元)")],
                    "cf investing":[list(df["报告日期"]).index("收回投资所收到的现金(万元)"),list(df["报告日期"]).index("投资活动产生的现金流量净额(万元)")],
                    "cf financing":[list(df["报告日期"]).index("吸收投资收到的现金(万元)"),list(df["报告日期"]).index("筹资活动产生的现金流量净额(万元)")],
                    "cf FX chg":list(df["报告日期"]).index("汇率变动对现金及现金等价物的影响(万元)"),
                    "cf net chg":[list(df["报告日期"]).index("现金及现金等价物净增加额(万元)"),list(df["报告日期"]).index("期末现金及现金等价物余额(万元)")],
                    "cf from profit":[list(df["报告日期"]).index("净利润(万元)"),list(df["报告日期"]).index("经营活动产生现金流量净额(万元)")],
                    "cf from invfin":[list(df["报告日期"]).index("债务转为资本(万元)"),list(df["报告日期"]).index("融资租入固定资产(万元)")],
                    "cf net chg2":[list(df["报告日期"]).index("现金的期末余额(万元)"),list(df["报告日期"]).index("现金及现金等价物的净增加额(万元)")]
                    }

    def rowdf(mystr):
        return pd.DataFrame([mystr]+[float("nan")]*(len(df.columns)-1),index=df.columns,columns=[0]).T
    
    xjllb = pd.concat([rowdf("一、经营活动产生的现金流量"),df.iloc[:tenK_structure["cf operating"][1]+1,:],
                       rowdf("二、投资活动产生的现金流量"),df.iloc[tenK_structure["cf investing"][0]:tenK_structure["cf investing"][1]+1,:],
                       rowdf("三、筹资活动产生的现金流量"),df.iloc[tenK_structure["cf financing"][0]:tenK_structure["cf financing"][1]+1,:],
                       rowdf("四、汇率变动对现金及现金等价物的影响"),df.iloc[tenK_structure["cf FX chg"]:tenK_structure["cf FX chg"]+1,:],
                       rowdf("五、现金及现金等价物净增加额"),df.iloc[tenK_structure["cf net chg"][0]:tenK_structure["cf net chg"][1]+1,:],
                       rowdf("1、将净利润调节为经营活动的现金流量"),df.iloc[tenK_structure["cf from profit"][0]:tenK_structure["cf from profit"][1]+1,:],
                       rowdf("2、不涉及现金收支的重大投资和筹资活动"),df.iloc[tenK_structure["cf from invfin"][0]:tenK_structure["cf from invfin"][1]+1,:],
                       rowdf("3、现金及现金等价物净变动"),df.iloc[tenK_structure["cf net chg2"][0]:tenK_structure["cf net chg2"][1]+1,:]],axis=0)
    
    xjllb.index = range(len(xjllb))
    #spacing
    def spacing(start_str,end_str,n=0):
        temp = [list(xjllb["报告日期"]).index(" "*n+start_str),list(xjllb["报告日期"]).index(" "*n+end_str)]
        xjllb.iloc[temp[0]:temp[1]+1,0] = map(lambda x:" "*4+x,xjllb.iloc[temp[0]:temp[1]+1,0])
    
    spacing("销售商品、提供劳务收到的现金(万元)","经营活动产生的现金流量净额(万元)")
    spacing("销售商品、提供劳务收到的现金(万元)","收到的其他与经营活动有关的现金(万元)",4)
    spacing("购买商品、接受劳务支付的现金(万元)","支付的其他与经营活动有关的现金(万元)",4)
    
    spacing("收回投资所收到的现金(万元)","投资活动产生的现金流量净额(万元)")
    spacing("收回投资所收到的现金(万元)","减少质押和定期存款所收到的现金(万元)",4)
    spacing("购建固定资产、无形资产和其他长期资产所支付的现金(万元)","增加质押和定期存款所支付的现金(万元)",4)

    spacing("吸收投资收到的现金(万元)","筹资活动产生的现金流量净额(万元)")
    spacing("吸收投资收到的现金(万元)","收到其他与筹资活动有关的现金(万元)",4)
    spacing("偿还债务支付的现金(万元)","支付其他与筹资活动有关的现金(万元)",4)

    spacing("汇率变动对现金及现金等价物的影响(万元)","汇率变动对现金及现金等价物的影响(万元)")

    spacing("净利润(万元)","经营活动产生现金流量净额(万元)")
    spacing("债务转为资本(万元)","融资租入固定资产(万元)")
    spacing("现金的期末余额(万元)","现金及现金等价物的净增加额(万元)")

    return xjllb
    
    

############################### main
seccode = "000002"
res = get_10K_raw(seccode)

df_zcfzb = format_zcfzb(res["zcfzb"])
df_lrb = format_lrb(res["lrb"])
df_xjllb = format_xjllb(res["xjllb"])



