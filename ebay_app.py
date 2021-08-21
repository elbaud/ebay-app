import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import requests

pd.set_option('display.max_colwidth', None)
# Page layout
## Page expands to full width
st.set_page_config(layout="wide")

#---------------------------------#
# Title

st.title('Ebay App')
st.markdown("""
""")

#---------------------------------#
# Page layout (continued)
col0 = st.sidebar
col1,col2 = st.beta_columns((3,1))

#---------------------------------#
search = col1.text_input("Item to search")


print('scraping..')
@st.cache()
def ebay(search):
    searc = search.replace(' ','')

    items = []
    status = []
    prices = []
    link = []
    
    # get num or results to filter final table
    url = f'https://www.ebay.co.uk/sch/i.html?_nkw={searc}'
    session = requests.Session()
    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}
    response = session.get(url, headers=user_agent)
    convert_soup = BeautifulSoup(response.text, 'html.parser')
    table = convert_soup.find('div',{'class':'srp-controls__control srp-controls__count'})
    num_res = table.find('h1').text
    nums = int(num_res.split(' ')[0])
    print(f'num results: {nums}')

    # iterate first 10 pages if any
    for page in range(1,10):
        
        try:

            url = f'https://www.ebay.co.uk/sch/i.html?_nkw={searc}&_pgn={page}&_sop=10' # sop=10 to order by newly listed
            #print(url)

            # set session object for cookies issue
            session = requests.Session()
            user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'}
            response = session.get(url, headers=user_agent)
            #print(response.status_code)

            # get table
            convert_soup = BeautifulSoup(response.text, 'html.parser')
            table = convert_soup.find('div',{'class':'srp-river-results clearfix'})

            for item in table.find_all('div',{'class':'s-item__wrapper clearfix'}):
                heading = item.find('h3') 
                try:
                    heading_data = heading.text
                    items.append(heading_data)

                    # status
                    s = item.find('span',{'class':'SECONDARY_INFO'})
                    try:
                        stat = s.text
                        status.append(stat)
                    except:
                        prices.append(np.nan)

                    # price
                    p = item.find('span',{'class':'s-item__price'})
                    try:
                        price = p.text
                        prices.append(price)
                    except:
                        prices.append(np.nan)

                    # link
                    l = item.find('a')['href']
                    link.append(l)

                except:
                    pass

        except:
            pass 

    # final table
    df = pd.DataFrame(list(zip(items, status ,prices, link)), columns=['item', 'status','price', 'link'])

    # remore records with x to x as price
    df = df.dropna()
    df['flag'] = 0
    df.loc[df['price'].str.contains('to'),'flag'] = 1
    df = df[df['flag'] == 0]

    # create LHR col flag if in title
    df['LHR'] = 'No'
    df['New listing'] = 'No'
    df.loc[df['item'].str.contains('LHR'),'LHR'] = 'Yes'
    df.loc[df['item'].str.contains('New listing'),'New listing'] = 'Yes'
    df['item'] = df['item'].str.replace('New listing','')
    
    df['curr'] = df['price'].str[:1]
    df['price2'] = df['price'].str[1:]
    df['price2'] = df['price2'].str.replace(',','')
    df['price2'] = df['price2'].astype(float)

    df = df.drop(['price','flag'], axis=1)
    df = df.rename(columns={"price2": "price"})

    return df.iloc[:nums,:]

def make_clickable(link):
    # target _blank to open new window
    # extract clickable text to display for your link
    text = link.split('=')[1]
    return f'<a target="_blank" href="{link}">{text}</a>'


if col1.button('Search'):
    #search = 'rtx 3060ti'
    df = ebay(search)
    # display table with results
    col1.subheader('Items table')

    # link is the column with hyperlinks
    df['link'] = df['link'].apply(make_clickable)
    df1 = df.to_html(escape=False)
    col1.write(df1, unsafe_allow_html=True)


    #col1.dataframe(df.to_html(escape=False)) #.loc[:,['user_name', 'text','favorite_count','retweet_count','created_at']].sort_values('favorite_count', ascending=False)

    # table stats
    lhr_avg = pd.DataFrame(df.groupby('LHR')['price'].mean())
    lhr_med = pd.DataFrame(df.groupby('LHR')['price'].median())

    nr_avg = pd.DataFrame(df.groupby('New listing')['price'].mean())
    nr_med = pd.DataFrame(df.groupby('New listing')['price'].median())

    sta_avg = pd.DataFrame(df.groupby('status')['price'].mean())
    sta_med = pd.DataFrame(df.groupby('status')['price'].median())

    col2.header('Prices Summary')
    col2.subheader('LHR price - avg')
    col2.dataframe(lhr_avg)
    
    col2.subheader('LHR price - median')
    col2.dataframe(lhr_med)
    
    col2.subheader('New listing - avg')
    col2.dataframe(nr_avg)
    
    col2.subheader('New listing - median')
    col2.dataframe(nr_med)

    col2.subheader('Status - avg')
    col2.dataframe(sta_avg)
    
    col2.subheader('Status - median')
    col2.dataframe(sta_med)

