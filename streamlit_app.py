import os
import time
import datetime
import streamlit as st
import pandas as pd
import plotly as plty
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
from plotly.subplots import make_subplots

def main():

    # Configuring web page
    st.set_page_config(layout="wide")

    # Loading datasets
    df_pts = pd.read_csv("points-injection.csv", sep=";")
    df_mois = pd.read_csv("production-mensuelle-biomethane.csv", sep=";")
    df_horaire = pd.read_csv("prod-nat-gaz-horaire-prov.csv", sep=";")

    list_years = [str(x) for x in range(2011, 2024, 1)]

    #
    st.image('logo.png')
    st.markdown("---")
    st.header("Production de Biométhane en France")
    st.write('\n')

    with st.spinner("Loading..."):
        time.sleep(2)
        
    #
    with st.expander("Jeux de Données"):
        tab1, tab2, tab3 = st.tabs(["points-injection.csv",
                                    "production-mensuelle-biomethane.csv",
                                    "prod-nat-gaz-horaire-prov.csv"])
        with tab1:
            st.dataframe(df_pts)
        with tab2:
            st.dataframe(df_mois)
        with tab3:
            st.dataframe(df_horaire)

    # KPIs
    st.subheader(" ")
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de sites", str(len(df_pts)), "15%")
    col2.metric("Capacité totale (GWh/an)", str(df_pts["Capacite de production (GWh/an)"].sum().round(1)), "28%")
    col3.metric("1er site", df_pts["Date de mise en service"].min(), "")

    # Layout
    st.subheader(" ")
    col1, col2 = st.columns([1,3])

    with col1:
        # Input widget
        annee = st.selectbox("Sélectionner une année:",
                             df_pts["Annee mise en service"].sort_values().unique().tolist(),
                             index=9,
                             key=1)
        
    #
    col1, col2, col3 = st.columns([1, 1, 1], gap="large")
    with col1:            
        #
        df_mois['Mois'] = df_mois['Mois'].apply(lambda x : dt.strptime(x + '-01', '%Y-%m-%d'))
        
        # plot
        fig = px.area(df_mois,
                       x="Mois",
                       y="Nombre de sites biomethane GRTgaz",
                       title="Sites Mis en Service par Mois")
        fig.add_vline(x = dt.strptime(str(annee) + '-01-01', '%Y-%m-%d'), line_color ="red")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Prepare data
        df_pts_bar = (df_pts[["Nom du site", "Capacite de production (GWh/an)"]]
                        .sort_values("Capacite de production (GWh/an)", ascending=False))
        #
        df_pts_bar["Nom du site"] = [x[:15] for x in df_pts_bar["Nom du site"]]

        st.subheader(" ")
        st.data_editor(
            df_pts_bar,
            column_config={
                            "Capacite de production (GWh/an)": st.column_config.ProgressColumn(
                                "Capacite de production (GWh/an)",
                                help="Capacite de production par Site (GWh/an)",
                                format="$%f",
                                min_value=0,
                                max_value=df_pts_bar["Capacite de production (GWh/an)"].max(),
                            ),
                        },
                    hide_index=True,

            width=1000
        )
      
        
    with col3:
        # Pepare Data
        df_pts_plot = df_pts[df_pts["Annee mise en service"] == annee][["Region", "Capacite de production (GWh/an)"]]

        # 5. Pie Plot
        fig = px.pie(df_pts_plot, 
                     values='Capacite de production (GWh/an)', 
                     names='Region', 
                     hole=.7,
                     title='Capacite de Production par Région')
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
      

    st.subheader(" ")
    col1, col2 = st.columns([1, 2], gap="large")
    with col1:
        st.subheader(" ")
        # Prepare Data
        df_sample = df_pts[df_pts["Annee mise en service"] == annee]
        df_sample[["latitude", "longitude"]] = df_sample["Coordonnees"].str.split(", ", expand=True).astype(float)

        # Map Plot
        st.map(df_sample[["latitude", "longitude"]].dropna(how="any"))

    with col2:
        # Prepare Data
        df_horaire[["annee", "mois", "jour"]] = df_horaire["Journée gazière"].str.split("-", expand=True)
        heures_liste = ["0" + str(i) + ":00" if i < 10 else str(i) + ":00" for i in range(24)]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            date_1 = st.date_input("Date de début:", datetime.date(annee, 1, 1))
        with col2:
            date_2 = st.date_input("Date de fin:", datetime.date(annee, 1, 15))
        with col3:
            h_min = st.selectbox("Heure de début:", (heures_liste), index=7)
        with col4:
            h_max = st.selectbox("Heure de fin:", (heures_liste), index=12)

        # filter month column
        month_1 = "0" + str(date_1.month) if date_1.month < 10 else str(date_1.month)
        month_2 = "0" + str(date_2.month) if date_2.month < 10 else str(date_2.month)
        # filter day column
        day_1 = "0" + str(date_1.day) if date_1.day < 10 else str(date_1.day)
        day_2 = "0" + str(date_2.day) if date_2.day < 10 else str(date_2.day)

        #
        df_horaire_week = df_horaire.loc[(df_horaire["annee"] >= str(date_1.year))
                                            & (df_horaire["annee"] <= str(date_2.year))
                                            & (df_horaire["mois"] >= month_1)
                                            & (df_horaire["mois"] <= month_2)
                                            & (df_horaire["jour"] >= day_1)
                                            & (df_horaire["jour"] <= day_2)]
        df_horaire_week = (df_horaire_week.drop(columns=["id",
                                                         "Annee/Mois",
                                                         "Production Journalière (MWh PCS)",
                                                         "Opérateur",
                                                         "Nombre de sites d'injection raccordés au réseau de transport",
                                                         "Statut de la donnée",
                                                         "annee",
                                                         "mois",
                                                         "jour"])
                                            .set_index("Journée gazière")
                                            .loc[:, h_min:h_max])

        # 5. Bar Plot
        fig = px.bar(df_horaire_week,
                     labels={"value": "Production (MWh PCS)",
                             "variable": "Heure"},
                     title=("Production Horaire Nationale"))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
