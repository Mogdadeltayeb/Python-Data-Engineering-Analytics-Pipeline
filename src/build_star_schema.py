import os
import pandas as pd

# مسارات الملفات
INPUT_FILE = os.path.join("data", "processed", "Saudi_Tourism_Analytics_Cleaned.xlsx")
OUTPUT_DIR = os.path.join("data", "processed", "star_schema")

def build_star_schema():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"الملف غير موجود في المسار: {INPUT_FILE}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("جاري قراءة ملف البيانات...")

    # 1. قراءة الجداول السبعة الرئيسية
    df_trends = pd.read_excel(INPUT_FILE, sheet_name="Quarterly_Trends")
    df_reg_kpis = pd.read_excel(INPUT_FILE, sheet_name="Regional_KPIs")
    df_city_kpis = pd.read_excel(INPUT_FILE, sheet_name="City_KPIs")
    df_emp_act = pd.read_excel(INPUT_FILE, sheet_name="Employment_Activity")
    df_emp_reg = pd.read_excel(INPUT_FILE, sheet_name="Employment_Region")
    df_est_act = pd.read_excel(INPUT_FILE, sheet_name="Establishments_Activity")
    df_est_reg = pd.read_excel(INPUT_FILE, sheet_name="Establishments_Region")

    # 2. بناء جداول الأبعاد (Dimension Tables)
    # Dim_Date (الأرباع الزمنية)
    dim_date = df_trends[["Quarter", "Quarter_Sort", "Quarter_Start_Date"]].drop_duplicates().reset_index(drop=True)
    dim_date["Date_ID"] = dim_date.index + 1

    # Dim_Region (المناطق الإدارية الـ 13)
    dim_region = df_reg_kpis[["Region"]].drop_duplicates().sort_values("Region").reset_index(drop=True)
    dim_region["Region_ID"] = dim_region.index + 1

    # Dim_City (المدن والمحافظات الـ 17)
    dim_city = df_city_kpis[["City"]].drop_duplicates().sort_values("City").reset_index(drop=True)
    dim_city["City_ID"] = dim_city.index + 1

    # Dim_Activity (الأنشطة السياحية الـ 12)
    dim_activity = df_emp_act[["Activity"]].drop_duplicates().sort_values("Activity").reset_index(drop=True)
    dim_activity["Activity_ID"] = dim_activity.index + 1

    # 3. بناء جداول الحقائق (Fact Tables) وربطها بمفاتيح الأبعاد (Foreign Keys)
    # Fact_Quarterly_Performance
    fact_quarterly = df_trends.merge(dim_date[["Quarter", "Date_ID"]], on="Quarter", how="left")
    fact_quarterly = fact_quarterly.drop(columns=["Quarter", "Quarter_Sort", "Quarter_Start_Date"])

    # Fact_Regional_Performance (Q2 2026)
    fact_regional = (
        df_reg_kpis
        .merge(df_emp_reg.drop(columns=["Reference_Period"]), on="Region", how="left")
        .merge(df_est_reg.drop(columns=["Reference_Period"]), on="Region", how="left")
        .merge(dim_region, on="Region", how="left")
        .drop(columns=["Region"])
    )

    # Fact_City_Performance (Q2 2026)
    fact_city = df_city_kpis.merge(dim_city, on="City", how="left").drop(columns=["City"])

    # Fact_Activity_Performance (Q2 2026)
    fact_activity = (
        df_emp_act
        .merge(df_est_act.drop(columns=["Reference_Period"]), on="Activity", how="left")
        .merge(dim_activity, on="Activity", how="left")
        .drop(columns=["Activity"])
    )

    # 4. حفظ جميع الجداول بصيغة CSV جاهزة لـ Power BI
    tables = {
        "Dim_Date": dim_date,
        "Dim_Region": dim_region,
        "Dim_City": dim_city,
        "Dim_Activity": dim_activity,
        "Fact_Quarterly_Performance": fact_quarterly,
        "Fact_Regional_Performance": fact_regional,
        "Fact_City_Performance": fact_city,
        "Fact_Activity_Performance": fact_activity,
    }

    for name, table in tables.items():
        out_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        table.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"✅ تم إنشاء: {name}.csv ({table.shape[0]} صف × {table.shape[1]} عمود)")

if __name__ == "__main__":
    build_star_schema()