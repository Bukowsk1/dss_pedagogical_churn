import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    df = pd.read_csv("data/dataset.csv")
    target_names = {
        0: 'Остался в школе',
        1: 'Перешел в другую школу',
        2: 'Ушел из сферы образования'
    }
    df['target_desc'] = df['target'].map(target_names)
    df['speciality'] = df['speciality'].fillna('Не указано')
    return df

df = load_data()

st.title("Панель руководителя образовательной организации")

st.sidebar.header("Параметры организации")

school_sizes = df.groupby('school_num')['teacher_id'].count().sort_values(ascending=False)
valid_schools = school_sizes.index.tolist()

selected_school = st.sidebar.selectbox(
    "Образовательная организация:",
    valid_schools,
    format_func=lambda x: f"Школа № {x} ({school_sizes[x]} записей)"
)

available_years = sorted(df[df['school_num'] == selected_school]['year'].unique())
selected_year = st.sidebar.selectbox("Учебный год:", available_years, index=len(available_years)-1)

school_df = df[(df['school_num'] == selected_school) & (df['year'] == selected_year)].copy()

specialities = sorted(school_df['speciality'].unique())
selected_spec = st.sidebar.multiselect("Предметные направления:", specialities, default=specialities)
filtered_school = school_df[school_df['speciality'].isin(selected_spec)]

k1, k2, k3, k4, k5 = st.columns(5)
total_staff = len(filtered_school)
k1.metric("Педагогов в штате", f"{total_staff}")

churn_teachers = len(filtered_school[filtered_school['target'] == 2])
churn_pct = (churn_teachers / total_staff * 100) if total_staff > 0 else 0
k2.metric("Уход из образования", f"{churn_pct:.1f}% ({churn_teachers})")

switch_teachers = len(filtered_school[filtered_school['target'] == 1])
k3.metric("Переход в другую школу", f"{switch_teachers}")

high_load_count = len(filtered_school[filtered_school['load_records_count'] >= 14])
k4.metric("С высокой нагрузкой (≥ 14 записей)", f"{high_load_count}")

bld_val = filtered_school['buildings_num'].median() if total_staff > 0 else 0
std_val = filtered_school['students_num'].median() if total_staff > 0 else 0
k5.metric("Контингент комплекса", f"{bld_val:.0f} корп. / {std_val:.0f} уч.")

st.markdown("---")

c1, c2 = st.columns(2)

with c1:
    fig1 = px.scatter(
        filtered_school,
        x="experience_age_pedagogic",
        y="subjects_count",
        size="load_records_count",
        color="target_desc",
        color_discrete_map={
            'Остался в школе': '#2b5c8f',
            'Перешел в другую школу': '#7570b3',
            'Ушел из сферы образования': '#d95f02'
        },
        hover_data=["teacher_id", "speciality", "age", "load_records_count"],
        labels={
            "experience_age_pedagogic": "Педагогический стаж (лет)",
            "subjects_count": "Число предметов",
            "load_records_count": "Записей нагрузки",
            "target_desc": "Статус"
        },
        title="Соотношение педагогического стажа и количества предметов"
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    spec_summary = filtered_school.groupby('speciality').agg(
        avg_load=('load_records_count', 'mean'),
        staff_count=('teacher_id', 'count')
    ).reset_index()

    fig2 = px.bar(
        spec_summary,
        x="speciality",
        y="avg_load",
        color="staff_count",
        color_continuous_scale="Blues",
        labels={"speciality": "Направление", "avg_load": "Ср. записей нагрузки", "staff_count": "Учителей"},
        title="Средняя интенсивность нагрузки по направлениям кафедр"
    )
    st.plotly_chart(fig2, use_container_width=True)