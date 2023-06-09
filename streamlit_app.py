import os
import math
import warnings
import folium
import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly as plty
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from plotly.subplots import make_subplots


def main():
    # Configuring web page
    st.set_page_config(layout="wide")

    # Loading datasets
    df_pts = pd.read_csv("points-injection.csv", sep=";")
    df_mois = pd.read_csv("production-mensuelle-biomethane.csv", sep=";")
    df_horaire = pd.read_csv("prod-nat-gaz-horaire-prov.csv", sep=";")

    list_years = [
        "2011",
        "2012",
        "2013",
        "2014",
        "2015",
        "2016",
        "2017",
        "2018",
        "2019",
        "2020",
        "2021",
        "2022",
        "2023",
    ]

    st.title("Production de Biométhane en France")
    st.markdown("---")

    st.subheader("0. Données")
    with st.expander("Données"):
        tab1, tab2, tab3 = st.tabs(
            [
                "points-injection.csv",
                "production-mensuelle-biomethane.csv",
                "prod-nat-gaz-horaire-prov.csv",
            ]
        )

    with tab1:
        st.dataframe(df_pts)
    with tab2:
        st.dataframe(df_mois)
    with tab3:
        st.dataframe(df_horaire)

    # KPIs
    st.subheader(" ")
    st.subheader(" ")
    st.subheader("1. Statistiques")
    col1_, col2_, col3_ = st.columns(3)
    col1_.metric("Nombre de sites", str(len(df_pts)), "15%")
    col2_.metric(
        "Capacité totale (GWh/an)",
        str(df_pts["Capacite de production (GWh/an)"].sum().round(1)),
        "28%",
    )
    col3_.metric("1er site", df_pts["Date de mise en service"].min(), "")

    # Layout
    st.subheader(" ")
    col1, col2 = st.columns([2, 1], gap="medium")
    with col1:
        st.subheader("2. Nombre de sites mis en service")
        min_year, max_year = st.select_slider(
            "Sélectionnez une période", options=list_years, value=("2013", "2022")
        )

        # Prepare data
        df_pts_annee = df_pts.groupby(by="Annee mise en service").count().reset_index()

        df_pts_annee_plot = df_pts_annee[
            (df_pts_annee["Annee mise en service"] >= int(min_year))
            & (df_pts_annee["Annee mise en service"] <= int(max_year))
        ].rename(columns={"Nom du site": "Nombre de sites"})

        # 1. Line Plot
        fig = px.area(
            df_pts_annee_plot,
            x="Annee mise en service",
            y="Nombre de sites",
            title="De " + str(min_year) + " à " + str(max_year),
        )

        # Show
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("3. Sites par capacité de production")
        # streamlit component
        top_value = st.slider("Top", 0, 30, 18)

        # Prepare data
        df_pts_bar = (
            df_pts[["Nom du site", "Capacite de production (GWh/an)"]]
            .sort_values("Capacite de production (GWh/an)", ascending=False)
            .head(top_value)
            .sort_values("Capacite de production (GWh/an)", ascending=True)
        )
        df_pts_bar["Nom du site"] = [x[:15] for x in df_pts_bar["Nom du site"]]

        # 3. Bar Plot
        fig = px.bar(
            df_pts_bar,
            y="Nom du site",
            x="Capacite de production (GWh/an)",
            orientation="h",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(" ")
    st.subheader(" ")
    st.subheader("4. Localisation des sites")

    # Prepare Data
    years = st.multiselect(
        "Sélectionnez une année de mise en service", list_years, default="2022"
    )
    if len(years) >= 1:
        df_sample = df_pts[
            df_pts["Annee mise en service"].astype(str).replace(",", "").isin(years)
        ]

        df_sample[["latitude", "longitude"]] = df_sample["Coordonnees"].str.split(
            ", ", expand=True
        )
        df_sample[["latitude", "longitude"]] = df_sample[
            ["latitude", "longitude"]
        ].astype(float)

        # 2. Map Plot
        st.map(df_sample[["latitude", "longitude"]].dropna(how="any"))

    else:
        st.write("No results.")

    st.subheader(" ")
    st.subheader("5. Capacite de production par région (%)")
    col1_ter, col2_ter, col3_ter, col4_ter = st.columns(4)

    with col1_ter:
        # streamlit component
        annee = st.selectbox(
            "Sélectionner une année:",
            (df_pts["Annee mise en service"].sort_values().unique().tolist()),
            index=10,
            key=1,
        )

    # Pepare Data
    df_pts_plot_n = df_pts[df_pts["Annee mise en service"] == annee][
        ["Region", "Capacite de production (GWh/an)"]
    ]
    df_pts_plot_n_1 = df_pts[df_pts["Annee mise en service"] == (annee-1)][
        ["Region", "Capacite de production (GWh/an)"]
    ]
    df_pts_plot_n_2 = df_pts[df_pts["Annee mise en service"] == (annee-2)][
        ["Region", "Capacite de production (GWh/an)"]
    ]

    # 5. Pie Plot
    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]],
        subplot_titles=["Année n-2", "Année n-1", "Année n", "2007"],
    )

    fig.add_trace(
        go.Pie(
            labels=df_pts_plot_n_2["Region"].to_list(),
            values=df_pts_plot_n_2["Capacite de production (GWh/an)"],
            # title='Année n-2',
            name="",
        ),
        1,
        1,
    )
    fig.add_trace(
        go.Pie(
            labels=df_pts_plot_n_1["Region"].to_list(),
            values=df_pts_plot_n_1["Capacite de production (GWh/an)"],
            # title='Année n-1',
            name="",
        ),
        1,
        2,
    )

    fig.add_trace(
        go.Pie(
            labels=df_pts_plot_n["Region"].to_list(),
            values=df_pts_plot_n["Capacite de production (GWh/an)"],
            # title='Année n',
            name="",
        ),
        1,
        3,
    )

    # Use `hole` to create a donut-like pie chart
    fig.update_traces(
        hole=0.7,
        hoverinfo="label+percent+name",
        pull=[0, 0, 0, 0.2, 0, 0, 0, 0, 0, 0, 0, 0],
        textposition="outside",
    )

    st.plotly_chart(fig, use_container_width=True)

    (col1,) = st.columns(1)
    with col1:
        st.subheader("6. Production nationale horaire")
        # Prepare Data
        df_horaire[["annee", "mois", "jour"]] = df_horaire["Journée gazière"].str.split(
            "-", expand=True
        )

        heures_liste = [
            "0" + str(i) + ":00" if i < 10 else str(i) + ":00" for i in range(24)
        ]

        col1_, col2_, col3_, col4_ = st.columns(4)
        with col1_:
            # streamlit component
            date_1 = st.date_input(
                "Sélectionnez une date de début:", datetime.date(2022, 1, 1)
            )
        with col2_:
            # streamlit component
            h_min = st.selectbox(
                "Sélectionnez une heure de début:", (heures_liste), index=6
            )
        with col3_:
            # streamlit component
            date_2 = st.date_input(
                "Sélectionnez une date de fin:", datetime.date(2022, 1, 21)
            )
        with col4_:
            # streamlit component
            h_max = st.selectbox(
                "Sélectionnez une heure de fin:", (heures_liste), index=12
            )

        # Prepare data
        month_1 = "0" + str(date_1.month) if date_1.month < 10 else str(date_1.month)
        month_2 = "0" + str(date_2.month) if date_2.month < 10 else str(date_2.month)

        day_1 = "0" + str(date_1.day) if date_1.day < 10 else str(date_1.day)
        day_2 = "0" + str(date_2.day) if date_2.day < 10 else str(date_2.day)

        df_horaire_week = df_horaire.loc[
            (df_horaire["annee"] >= str(date_1.year))
            & (df_horaire["annee"] <= str(date_2.year))
            & (df_horaire["mois"] >= month_1)
            & (df_horaire["mois"] <= month_2)
            & (df_horaire["jour"] >= day_1)
            & (df_horaire["jour"] <= day_2)
        ]

        df_horaire_week = (
            df_horaire_week.drop(
                columns=[
                    "id",
                    "Annee/Mois",
                    #'Journée gazière',
                    "Production Journalière (MWh PCS)",
                    "Opérateur",
                    "Nombre de sites d'injection raccordés au réseau de transport",
                    "Statut de la donnée",
                    "annee",
                    "mois",
                    "jour",
                ]
            )
            .set_index("Journée gazière")
            .loc[:, h_min:h_max]
        )

        # 4. Bar Plot
        fig = px.bar(
            df_horaire_week,
            labels={
                "value": "Production (MWh PCS)",
                "variable": "Heure",
            },
            title=("Production Horaire Nationale"),
        )
        # Show
        st.plotly_chart(fig, use_container_width=True)


main()
