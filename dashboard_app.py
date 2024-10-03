import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
from datetime import timedelta
import sys

def create_monthly_orders_df(df):
    monthly_orders_df = df.resample(rule='ME', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    
    return monthly_orders_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max", 
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

def create_category_rating_df(df):
    category_rating_df = df.groupby('product_category_name_english').agg({
        'review_score': ['mean', 'count']
    }).reset_index()
    
    category_rating_df.columns = ['product_category_name_english', 'average_rating', 'total_reviews']

    category_rating_df = category_rating_df.sort_values(by='average_rating', ascending=False)
    
    return category_rating_df

all_df = pd.df = pd.read_excel("all_data.xlsx")

all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

main_df = all_df.copy()

monthly_orders_df = create_monthly_orders_df(main_df)
rfm_df = create_rfm_df(main_df)
category_rating_df = create_category_rating_df(main_df)

# 1. Performan Penjualan dalam 6 Bulan Terakhir
st.markdown("<h1 style='text-align: center; color: black;'>✨ E-Commerce Dashboard ✨</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader('Performa Penjualan dalam 6 Bulan Terakhir')

last_six_months = main_df[main_df['order_purchase_timestamp'] >= (main_df['order_purchase_timestamp'].max() - pd.DateOffset(months=6))]
monthly_orders_df = create_monthly_orders_df(last_six_months)

# Print the monthly orders DataFrame to debug
print(monthly_orders_df)

col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)

with col2:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)

# Plotting the data
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(monthly_orders_df["order_purchase_timestamp"], monthly_orders_df["order_count"], marker='o', linewidth=3, color="navy")
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
ax.set_title("Total Orders Over Time (Last 6 Months)", fontsize=25)
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Total Orders", fontsize=20)

# Display the plot
st.pyplot(fig)


# 2. Pola Pembelian Pelanggan dalam Setahun Terakhir
st.subheader('Pola Pembelian Pelanggan dalam Setahun Terakhir')

current_date = main_df['order_purchase_timestamp'].max()
one_year_ago = current_date - timedelta(days=365)
filtered_data = main_df[main_df['order_purchase_timestamp'] >= one_year_ago]

# Hitung RFM
rfm_df = create_rfm_df(filtered_data)

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(15, 30))  # Adjusted 

# By Recency
sns.barplot(y="customer_id", x="recency", data=rfm_df.sort_values(by="recency", ascending=True).head(20), color="skyblue", ax=ax[0])
ax[0].set_xlabel("Recency (days)", fontsize=20)
ax[0].set_ylabel("Customer ID", fontsize=20)
ax[0].set_title("Top 20 Customers by Recency", loc="center", fontsize=25)

# By Frequency
sns.barplot(y="customer_id", x="frequency", data=rfm_df.sort_values(by="frequency", ascending=False).head(20), color="violet", ax=ax[1])
ax[1].set_xlabel("Frequency", fontsize=20)
ax[1].set_ylabel("Customer ID", fontsize=20)
ax[1].set_title("Top 20 Customers by Frequency", loc="center", fontsize=25)

# By Monetary
sns.barplot(y="customer_id", x="monetary", data=rfm_df.sort_values(by="monetary", ascending=False).head(20), color="cyan", ax=ax[2])
ax[2].set_xlabel("Monetary Value", fontsize=20)
ax[2].set_ylabel("Customer ID", fontsize=20)
ax[2].set_title("Top 20 Customers by Monetary Value", loc="center", fontsize=25)

st.pyplot(fig)


# 3. Distribusi Rating Berdasarkan Kategori Produk
st.subheader('Distribusi Rating Berdasarkan Kategori Produk')

fig, ax = plt.subplots(figsize=(8, 13))
sns.barplot(x='average_rating', y='product_category_name_english', data=category_rating_df, color='yellow', ax=ax)
plt.title('Rata-rata Rating Produk Berdasarkan Kategori', fontsize=16)
plt.xlabel('Rata-rata Rating', fontsize=14)
plt.ylabel('Kategori Produk', fontsize=14)

st.pyplot(fig)
