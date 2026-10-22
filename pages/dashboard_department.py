import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    df = pd.read_csv("data/dataset.csv")
    df['district'] = df['district'].fillna('Не указан')
    return df

df = load_data()

st.title("Сводный мониторинг Органа управления образованием")

st.sidebar.header("Параметры выборки")

available_years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("Учебный год:", available_years, index=len(available_years)-1)

districts = sorted(df['district'].unique())
selected_districts = st.sidebar.multiselect("Округа региона:", districts, default=districts)

min_staff_threshold = st.sidebar.slider("Минимальный штат школы для анализа:", 5, 50, 15)

filtered_df = df[(df['year'] == selected_year) & (df['district'].isin(selected_districts))].copy()

k1, k2, k3, k4 = st.columns(4)
total_teachers = len(filtered_df)

k1.metric("Педагогический корпус", f"{total_teachers:d}".replace(",", " "))

schools_count = filtered_df['school_num'].nunique()
k2.metric("Образовательных организаций", f"{schools_count}")

regional_churn = (filtered_df['target'] == 2).mean() * 100 if total_teachers > 0 else 0
k3.metric("Средний отток по региону", f"{regional_churn:.1f}%")

high_qual_share = (filtered_df['category_qual'] == 3).mean() * 100 if total_teachers > 0 else 0
k4.metric("Доля высшей квалификации", f"{high_qual_share:.1f}%")

st.markdown("---")

school_stats = filtered_df.groupby(['school_num', 'district']).agg(
    staff_size=('teacher_id', 'count'),
    churn_rate=('target', lambda s: (s == 2).mean() * 100),
    avg_load=('load_records_count', 'mean'),
    high_qual_rate=('category_qual', lambda s: (s == 3).mean() * 100),
    students_num=('students_num', 'median')
).reset_index()

analyzed_schools = school_stats[school_stats['staff_size'] >= min_staff_threshold]

c1, c2 = st.columns(2)

with c1:
    fig1 = px.scatter(
        analyzed_schools,
        x="avg_load",
        y="churn_rate",
        size="staff_size",
        color="district",
        hover_data=["school_num", "staff_size", "high_qual_rate"],
        labels={
            "avg_load": "Среднее число записей нагрузки на педагога",
            "churn_rate": "Текучесть школы (%)",
            "district": "Округ",
            "staff_size": "Штат"
        },
        title="Зависимость текучести от средней нагрузки по школам"
    )
    fig1.add_hline(y=regional_churn, line_dash="dot", line_color="red", annotation_text="Средний отток по региону")
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    district_summary = filtered_df.groupby('district').agg(
        churn_pct=('target', lambda s: (s == 2).mean() * 100),
        high_qual_pct=('category_qual', lambda s: (s == 3).mean() * 100)
    ).reset_index()

    fig2 = px.bar(
        district_summary,
        x="district",
        y=["churn_pct", "high_qual_pct"],
        barmode="group",
        labels={"value": "Доля учителей (%)", "variable": "Метрика", "district": "Округ"},
        color_discrete_map={"churn_pct": "#d95f02", "high_qual_pct": "#2b5c8f"},
        title="Сопоставление округов: текучесть кадров и высшая категория"
    )
    st.plotly_chart(fig2, use_container_width=True)