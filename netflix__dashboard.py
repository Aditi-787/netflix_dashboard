import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os
import requests
import threading
from datetime import datetime

# ─────────────────────────────────────────────
#  COLOR PALETTE
# ─────────────────────────────────────────────
BG   = "#0D0D0D"
CARD = "#1A1A1A"
FG   = "#F0F0F0"
RED  = "#E50914"
GOLD = "#F5C518"
MUTED= "#888888"
GOOD = "#21C97C"
WARN = "#E76F51"

FILE_PATH = "C:/Users/Dell/DASHBOARD/netflix_titles.csv"

# ─────────────────────────────────────────────
#  DATA LOADING & CLEANING
# ─────────────────────────────────────────────
def load_data():
    df = pd.read_csv(FILE_PATH)
    df = df.drop_duplicates().copy()
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df['director']        = df['director'].fillna('Unknown')
    df['cast']            = df['cast'].fillna('Unknown')
    df['country']         = df['country'].fillna('Unknown')
    df['rating']          = df['rating'].fillna('Not Rated')
    df['duration']        = df['duration'].fillna('0 min')
    df['date_added']      = pd.to_datetime(df['date_added'].str.strip(), errors='coerce')
    df['year_added']      = df['date_added'].dt.year
    df['month_added']     = df['date_added'].dt.month
    df['duration_mins']   = df['duration'].str.extract(r'(\d+)').astype(float)
    df['primary_country'] = df['country'].str.split(',').str[0].str.strip()
    df['primary_genre']   = df['listed_in'].str.split(',').str[0].str.strip()
    return df


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def lbl(parent, text, size=11, bold=False, color=FG, **kw):
    font = ("Helvetica", size, "bold" if bold else "normal")
    return tk.Label(parent, text=text,
                    bg=kw.pop("bg", parent["bg"]),
                    fg=color, font=font, **kw)


def style_ax(ax, title=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=FG, labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    if title:
        ax.set_title(title, color=FG, fontsize=10, pad=6)


# ─────────────────────────────────────────────
#  BUILD DASHBOARD
# ─────────────────────────────────────────────
def build_dashboard(root, df):
    root.title("Netflix Content Analytics Dashboard")
    root.configure(bg=BG)
    root.state("zoomed")

    # ══════════════════════════════════════════
    #  HEADER
    # ══════════════════════════════════════════
    header = tk.Frame(root, bg=BG)
    header.pack(fill="x", padx=20, pady=(10, 4))
    lbl(header, "▶ NETFLIX", 26, bold=True, color=RED).pack(side="left")
    lbl(header, "  Content Analytics Dashboard", 20, color=FG).pack(side="left", pady=4)
    lbl(header, "Kaggle – Netflix Movies and TV Shows", 9, color=MUTED).pack(side="right", pady=8)

    # ══════════════════════════════════════════
    #  GLOBAL FILTER BAR
    # ══════════════════════════════════════════
    fbar = tk.Frame(root, bg="#111111", pady=7)
    fbar.pack(fill="x", padx=10, pady=(0, 4))

    lbl(fbar, "  FILTERS:", 9, bold=True, color=GOLD, bg="#111111").pack(side="left", padx=(6, 10))

    lbl(fbar, "Type:", 9, color=MUTED, bg="#111111").pack(side="left")
    type_var = tk.StringVar(value="All")
    type_cb  = ttk.Combobox(fbar, textvariable=type_var, width=10,
                             values=["All", "Movie", "TV Show"], state="readonly")
    type_cb.pack(side="left", padx=(2, 12))

    lbl(fbar, "Country:", 9, color=MUTED, bg="#111111").pack(side="left")
    top_countries = ["All"] + list(
        df[df['primary_country'] != 'Unknown']['primary_country']
        .value_counts().head(25).index)
    country_var = tk.StringVar(value="All")
    country_cb  = ttk.Combobox(fbar, textvariable=country_var, width=16,
                                values=top_countries, state="readonly")
    country_cb.pack(side="left", padx=(2, 12))

    lbl(fbar, "Rating:", 9, color=MUTED, bg="#111111").pack(side="left")
    rating_list = ["All"] + list(df['rating'].value_counts().head(12).index)
    rating_var  = tk.StringVar(value="All")
    rating_cb   = ttk.Combobox(fbar, textvariable=rating_var, width=10,
                                values=rating_list, state="readonly")
    rating_cb.pack(side="left", padx=(2, 12))

    lbl(fbar, "Year:", 9, color=MUTED, bg="#111111").pack(side="left")
    yr_from = tk.StringVar(value="2015")
    yr_to   = tk.StringVar(value="2021")
    ttk.Combobox(fbar, textvariable=yr_from, width=6,
                 values=[str(y) for y in range(2008, 2022)],
                 state="readonly").pack(side="left", padx=2)
    lbl(fbar, "–", 10, color=MUTED, bg="#111111").pack(side="left")
    ttk.Combobox(fbar, textvariable=yr_to, width=6,
                 values=[str(y) for y in range(2008, 2022)],
                 state="readonly").pack(side="left", padx=(2, 12))

    apply_btn = tk.Button(fbar, text=" Apply ", bg=RED, fg=FG,
                          font=("Helvetica", 9, "bold"), relief="flat", cursor="hand2")
    apply_btn.pack(side="left", padx=4)
    reset_btn = tk.Button(fbar, text="Reset", bg=CARD, fg=MUTED,
                          font=("Helvetica", 9), relief="flat", cursor="hand2")
    reset_btn.pack(side="left", padx=4)

    filter_status = lbl(fbar, "Showing: All data", 9, color=GOOD, bg="#111111")
    filter_status.pack(side="right", padx=14)

    cs = ttk.Style()
    cs.theme_use("default")
    cs.configure("TCombobox", fieldbackground=CARD, background=CARD,
                 foreground=FG, selectbackground=RED, selectforeground=FG)

    # ══════════════════════════════════════════
    #  TAB NOTEBOOK
    # ══════════════════════════════════════════
    ns = ttk.Style()
    ns.configure("TNotebook",     background=BG,   borderwidth=0)
    ns.configure("TNotebook.Tab", background=CARD, foreground=FG,
                 padding=(20, 9), font=("Helvetica", 10, "bold"))
    ns.map("TNotebook.Tab",       background=[("selected", RED)])

    nb = ttk.Notebook(root, style="TNotebook")
    nb.pack(fill="both", expand=True, padx=10, pady=6)

    # ══════════════════════════════════════════
    #  PAGE 1 — Executive Overview
    # ══════════════════════════════════════════
    p1 = tk.Frame(nb, bg=BG)
    nb.add(p1, text="  Overview  ")

    kpi_row = tk.Frame(p1, bg=BG)
    kpi_row.pack(fill="x", padx=14, pady=(10, 6))

    kpi_labels = {}
    kpi_defs = [
        ("total",    "Total Titles",   FG),
        ("movies",   "Movies",         GOLD),
        ("shows",    "TV Shows",       GOOD),
        ("countries","Countries",      RED),
        ("avg_dur",  "Avg Movie Dur.", "#00BFFF"),
        ("top_genre","Top Genre",      WARN),
    ]
    for key, title, color in kpi_defs:
        card = tk.Frame(kpi_row, bg=CARD, padx=14, pady=12)
        card.pack(side="left", fill="x", expand=True, padx=5)
        lbl(card, title, 9, color=MUTED, bg=CARD).pack(anchor="w")
        v = lbl(card, "—", 18, bold=True, color=color, bg=CARD)
        v.pack(anchor="w")
        kpi_labels[key] = v

    chart_frame1 = tk.Frame(p1, bg=BG)
    chart_frame1.pack(fill="both", expand=True, padx=14, pady=4)
    p1_holder = {"canvas": None}

    def draw_overview(dff):
        if p1_holder["canvas"]:
            p1_holder["canvas"].get_tk_widget().destroy()
        movies_ = dff[dff['type'] == 'Movie']
        shows_  = dff[dff['type'] == 'TV Show']
        total_  = len(dff)
        dur_    = movies_['duration_mins'].dropna()
        dur_    = dur_[(dur_ > 20) & (dur_ < 300)]

        kpi_labels["total"].config(text=f"{total_:,}")
        kpi_labels["movies"].config(text=f"{len(movies_):,}")
        kpi_labels["shows"].config(text=f"{len(shows_):,}")
        kpi_labels["countries"].config(text=f"{dff['primary_country'].nunique():,}")
        kpi_labels["avg_dur"].config(text=f"{dur_.mean():.0f} min" if len(dur_) else "—")
        tg = dff['primary_genre'].value_counts().idxmax() if total_ else "—"
        kpi_labels["top_genre"].config(text=str(tg)[:14])

        fig = Figure(figsize=(13, 5), dpi=92)
        fig.patch.set_facecolor(BG)

        yr_data = dff['year_added'].dropna()
        yearly  = (dff[dff['year_added'].between(yr_data.min(), yr_data.max())]
                   .groupby('year_added')['show_id'].count())

        ax1 = fig.add_subplot(231)
        ax1.bar(yearly.index.astype(int), yearly.values, color=RED, edgecolor="none", width=0.7)
        style_ax(ax1, "Titles Added Per Year")
        ax1.tick_params(axis='x', rotation=35)

        ax2 = fig.add_subplot(232)
        counts = dff['type'].value_counts()
        if len(counts):
            ax2.pie(counts.values, labels=counts.index,
                    colors=[RED, GOLD], autopct='%1.1f%%',
                    textprops={'color': FG, 'fontsize': 10},
                    wedgeprops=dict(width=0.48))
        style_ax(ax2, "Movies vs TV Shows")

        ax3 = fig.add_subplot(233)
        top_c = (dff[dff['primary_country'] != 'Unknown']['primary_country']
                 .value_counts().head(8))
        ax3.barh(top_c.index[::-1], top_c.values[::-1], color=GOLD, edgecolor="none")
        style_ax(ax3, "Top Countries")

        ax4 = fig.add_subplot(234)
        rat = dff['rating'].value_counts().head(8)
        ax4.bar(rat.index, rat.values, color=GOOD, edgecolor="none")
        style_ax(ax4, "Content by Rating")
        ax4.tick_params(axis='x', rotation=30)

        ax5 = fig.add_subplot(235)
        mnames  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly = dff.groupby('month_added')['show_id'].count().reindex(range(1,13), fill_value=0)
        ax5.plot(mnames, monthly.values, marker='o', color=RED, linewidth=2)
        ax5.fill_between(mnames, monthly.values, color=RED, alpha=0.15)
        style_ax(ax5, "Titles Added by Month")
        ax5.tick_params(axis='x', rotation=30)

        ax6 = fig.add_subplot(236)
        ax6.axis("off"); ax6.set_facecolor(CARD)
        peak  = int(yearly.idxmax()) if len(yearly) else "—"
        top_r = dff['rating'].value_counts().idxmax() if total_ else "—"
        ax6.text(0.05, 0.92, "Key Insights", color=FG, fontsize=12, weight="bold",
                 transform=ax6.transAxes)
        ax6.text(0.05, 0.70,
                 f"• Total: {total_:,} titles\n"
                 f"• Peak year: {peak}\n"
                 f"• Top rating: {top_r}\n"
                 f"• Top genre: {tg}\n"
                 f"• Avg runtime: {dur_.mean():.0f} min" if len(dur_) else "",
                 color=FG, fontsize=10, va="top", transform=ax6.transAxes)

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame1)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        p1_holder["canvas"] = canvas

    draw_overview(df)

    # ══════════════════════════════════════════
    #  PAGE 2 — Genre Analysis
    # ══════════════════════════════════════════
    p2 = tk.Frame(nb, bg=BG)
    nb.add(p2, text="  Genre Analysis  ")

    lbl(p2, "Genre & Content Type Analysis", 18, bold=True).pack(anchor="w", padx=20, pady=(14,2))
    lbl(p2, "Breakdown by listed genres", 9, color=MUTED).pack(anchor="w", padx=20)

    g_ctrl = tk.Frame(p2, bg=BG)
    g_ctrl.pack(fill="x", padx=20, pady=6)
    lbl(g_ctrl, "Segment:", 9, color=MUTED, bg=BG).pack(side="left")
    seg_var = tk.StringVar(value="Both")
    seg_cb  = ttk.Combobox(g_ctrl, textvariable=seg_var, width=12,
                            values=["Both","Movie","TV Show"], state="readonly")
    seg_cb.pack(side="left", padx=6)

    g_frame = tk.Frame(p2, bg=BG)
    g_frame.pack(fill="both", expand=True, padx=14, pady=4)
    g_holder = {"canvas": None}

    def draw_genre(dff, seg="Both"):
        if g_holder["canvas"]:
            g_holder["canvas"].get_tk_widget().destroy()
        sub = dff if seg == "Both" else dff[dff['type'] == seg]
        fig = Figure(figsize=(14, 5.5), dpi=92)
        fig.patch.set_facecolor(BG)

        ax1 = fig.add_subplot(121)
        genres = sub['listed_in'].dropna().str.split(', ').explode().value_counts().head(14)
        clrs   = [RED if i < 3 else GOLD if i < 7 else MUTED for i in range(len(genres))]
        ax1.barh(genres.index[::-1], genres.values[::-1], color=clrs[::-1], edgecolor="none")
        style_ax(ax1, f"Top Genres ({seg})")

        ax2 = fig.add_subplot(122)
        mg = dff[dff['type']=='Movie']['listed_in'].dropna().str.split(', ').explode().value_counts().head(8)
        sg = dff[dff['type']=='TV Show']['listed_in'].dropna().str.split(', ').explode().value_counts().head(8)
        common = list(dict.fromkeys(list(mg.index)+list(sg.index)))[:8]
        x = np.arange(len(common))
        ax2.bar(x-0.2, [mg.get(g,0) for g in common], 0.38, label="Movies",   color=RED,  edgecolor="none")
        ax2.bar(x+0.2, [sg.get(g,0) for g in common], 0.38, label="TV Shows", color=GOLD, edgecolor="none")
        ax2.set_xticks(x)
        ax2.set_xticklabels(common, rotation=35, ha='right', fontsize=7, color=FG)
        ax2.legend(facecolor=CARD, labelcolor=FG)
        style_ax(ax2, "Genre Split: Movies vs TV Shows")

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=g_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        g_holder["canvas"] = canvas

    draw_genre(df)
    seg_cb.bind("<<ComboboxSelected>>", lambda e: draw_genre(df, seg_var.get()))

    # ══════════════════════════════════════════
    #  PAGE 3 — Country Intelligence
    # ══════════════════════════════════════════
    p3 = tk.Frame(nb, bg=BG)
    nb.add(p3, text="  Country Intelligence  ")

    lbl(p3, "Country-wise Content Intelligence", 18, bold=True).pack(anchor="w", padx=20, pady=(14,2))
    lbl(p3, "Ranked by total titles, movies, and TV shows", 9, color=MUTED).pack(anchor="w", padx=20)

    c_ctrl = tk.Frame(p3, bg=BG)
    c_ctrl.pack(fill="x", padx=20, pady=6)
    lbl(c_ctrl, "Sort by:", 9, color=MUTED, bg=BG).pack(side="left")
    sort_var = tk.StringVar(value="Total Titles")
    sort_cb  = ttk.Combobox(c_ctrl, textvariable=sort_var, width=14,
                             values=["Total Titles","Movies","TV Shows","Movie Share %"],
                             state="readonly")
    sort_cb.pack(side="left", padx=4)
    lbl(c_ctrl, "Rows:", 9, color=MUTED, bg=BG).pack(side="left", padx=(14,2))
    rows_var = tk.StringVar(value="10")
    rows_cb  = ttk.Combobox(c_ctrl, textvariable=rows_var, width=5,
                             values=["5","10","15","20"], state="readonly")
    rows_cb.pack(side="left", padx=2)

    c3_main = tk.Frame(p3, bg=BG)
    c3_main.pack(fill="both", expand=True, padx=14, pady=6)
    c3_tbl   = tk.Frame(c3_main, bg=CARD)
    c3_tbl.pack(side="left", fill="both", expand=True, padx=(0,10))
    c3_chart = tk.Frame(c3_main, bg=CARD)
    c3_chart.pack(side="left", fill="both", expand=True)
    c3_holder = {"canvas": None, "widgets": []}

    def draw_country(dff, sort_col="Total Titles", n=10):
        for w in c3_holder["widgets"]: w.destroy()
        c3_holder["widgets"] = []
        if c3_holder["canvas"]: c3_holder["canvas"].get_tk_widget().destroy()

        cdf   = dff[dff['primary_country'] != 'Unknown']
        stats = cdf.groupby('primary_country').agg(
            total=('show_id','count'),
            movies=('type', lambda x: (x=='Movie').sum()),
            shows=('type',  lambda x: (x=='TV Show').sum()),
        )
        stats['share'] = (stats['movies']/stats['total']*100).round(1)
        col_map = {"Total Titles":"total","Movies":"movies","TV Shows":"shows","Movie Share %":"share"}
        stats = stats.sort_values(col_map[sort_col], ascending=False).head(n)

        for i, h in enumerate(['COUNTRY','TOTAL','MOVIES','TV SHOWS','MOVIE %']):
            w = tk.Label(c3_tbl, text=h, bg=CARD, fg=RED, font=("Helvetica",9,"bold"))
            w.grid(row=0, column=i, padx=16, pady=10, sticky='w')
            c3_holder["widgets"].append(w)

        for r, (country, row) in enumerate(stats.iterrows(), 1):
            cbg  = '#1F1F1F' if r%2==0 else CARD
            vals = [country, f"{row['total']:,}", f"{row['movies']:,}",
                    f"{row['shows']:,}", f"{row['share']:.1f}%"]
            for c, val in enumerate(vals):
                color = FG
                if c == 4:
                    color = GOLD if row['share']>70 else GOOD if row['share']>50 else WARN
                w = tk.Label(c3_tbl, text=val, bg=cbg, fg=color, font=("Helvetica",10))
                w.grid(row=r, column=c, padx=16, pady=7, sticky='w')
                c3_holder["widgets"].append(w)

        fig = Figure(figsize=(5,5), dpi=90)
        fig.patch.set_facecolor(CARD)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(CARD)
        t5  = stats.head(5)
        ax.bar(t5.index, t5['movies'], color=RED,  label='Movies',   edgecolor="none")
        ax.bar(t5.index, t5['shows'],  color=GOLD, label='TV Shows', edgecolor="none", bottom=t5['movies'])
        ax.set_title('Stacked Mix (Top 5)', color=FG, fontsize=10)
        ax.tick_params(colors=FG, labelsize=8, axis='x', rotation=20)
        ax.tick_params(colors=FG, axis='y')
        ax.legend(facecolor=CARD, labelcolor=FG, fontsize=8)
        for sp in ax.spines.values(): sp.set_visible(False)
        fig.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(fig, master=c3_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=8, pady=8)
        c3_holder["canvas"] = canvas

    draw_country(df)
    sort_cb.bind("<<ComboboxSelected>>", lambda e: draw_country(df, sort_var.get(), int(rows_var.get())))
    rows_cb.bind("<<ComboboxSelected>>", lambda e: draw_country(df, sort_var.get(), int(rows_var.get())))

    # ══════════════════════════════════════════
    #  PAGE 4 — Duration & Ratings
    # ══════════════════════════════════════════
    p4 = tk.Frame(nb, bg=BG)
    nb.add(p4, text="  Duration & Ratings  ")

    lbl(p4, "Duration & Ratings Deep Dive", 18, bold=True).pack(anchor="w", padx=20, pady=(14,2))
    lbl(p4, "Movie runtimes, TV seasons, audience rating distribution", 9, color=MUTED).pack(anchor="w", padx=20)

    d_ctrl = tk.Frame(p4, bg=BG)
    d_ctrl.pack(fill="x", padx=20, pady=6)
    lbl(d_ctrl, "Histogram bins:", 9, color=MUTED, bg=BG).pack(side="left")
    bins_var = tk.StringVar(value="30")
    bins_cb  = ttk.Combobox(d_ctrl, textvariable=bins_var, width=6,
                             values=["10","20","30","40","50"], state="readonly")
    bins_cb.pack(side="left", padx=6)

    d_frame  = tk.Frame(p4, bg=BG)
    d_frame.pack(fill="both", expand=True, padx=14, pady=4)
    d_holder = {"canvas": None}

    def draw_duration(dff, bins=30):
        if d_holder["canvas"]: d_holder["canvas"].get_tk_widget().destroy()
        movies_ = dff[dff['type']=='Movie']
        shows_  = dff[dff['type']=='TV Show']
        fig = Figure(figsize=(14, 5.5), dpi=92)
        fig.patch.set_facecolor(BG)

        ax1 = fig.add_subplot(131)
        dur = movies_['duration_mins'].dropna()
        dur = dur[(dur>20)&(dur<300)]
        if len(dur):
            ax1.hist(dur, bins=bins, color=RED, edgecolor="none", alpha=0.9)
            ax1.axvline(dur.mean(), color=GOLD, linestyle='--', linewidth=1.5,
                        label=f"Avg: {dur.mean():.0f} min")
            ax1.legend(facecolor=CARD, labelcolor=FG, fontsize=8)
        style_ax(ax1, "Movie Duration Distribution")

        ax2 = fig.add_subplot(132)
        tv_s = shows_['duration'].str.extract(r'(\d+)').astype(float).squeeze()
        sc   = tv_s.value_counts().sort_index().head(10)
        if len(sc):
            ax2.bar(sc.index.astype(int), sc.values, color=GOLD, edgecolor="none")
        ax2.set_xlabel("Seasons", color=MUTED, fontsize=9)
        style_ax(ax2, "TV Shows by Seasons")

        ax3 = fig.add_subplot(133)
        ro = dff['rating'].value_counts().head(10)
        if len(ro):
            clrs = [RED if r in ['TV-MA','R'] else GOLD if r in ['TV-14','PG-13'] else GOOD
                    for r in ro.index]
            ax3.pie(ro.values, labels=ro.index, colors=clrs, autopct='%1.0f%%',
                    textprops={'color':FG,'fontsize':7}, wedgeprops=dict(width=0.52))
        style_ax(ax3, "Audience Rating Mix")

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=d_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        d_holder["canvas"] = canvas

    draw_duration(df)
    bins_cb.bind("<<ComboboxSelected>>", lambda e: draw_duration(df, int(bins_var.get())))

    # ══════════════════════════════════════════
    #  PAGE 5 — YoY Trends
    # ══════════════════════════════════════════
    p5 = tk.Frame(nb, bg=BG)
    nb.add(p5, text="  YoY Trends  ")

    lbl(p5, "Year-over-Year Growth Trends", 18, bold=True).pack(anchor="w", padx=20, pady=(14,2))
    lbl(p5, "How Netflix content library evolved over time", 9, color=MUTED).pack(anchor="w", padx=20)

    y_ctrl = tk.Frame(p5, bg=BG)
    y_ctrl.pack(fill="x", padx=20, pady=6)
    lbl(y_ctrl, "From:", 9, color=MUTED, bg=BG).pack(side="left")
    yf_var = tk.StringVar(value="2015")
    yf_cb  = ttk.Combobox(y_ctrl, textvariable=yf_var, width=6,
                           values=[str(y) for y in range(2008,2022)], state="readonly")
    yf_cb.pack(side="left", padx=4)
    lbl(y_ctrl, "To:", 9, color=MUTED, bg=BG).pack(side="left", padx=(10,0))
    yt_var = tk.StringVar(value="2021")
    yt_cb  = ttk.Combobox(y_ctrl, textvariable=yt_var, width=6,
                           values=[str(y) for y in range(2008,2022)], state="readonly")
    yt_cb.pack(side="left", padx=4)

    y5_frame  = tk.Frame(p5, bg=BG)
    y5_frame.pack(fill="both", expand=True, padx=14, pady=4)
    y5_holder = {"canvas": None}

    def draw_yoy(dff, yf=2015, yt=2021):
        if y5_holder["canvas"]: y5_holder["canvas"].get_tk_widget().destroy()
        sub = dff[dff['year_added'].between(yf, yt)]
        yoy = sub.groupby(['year_added','type'])['show_id'].count().unstack(fill_value=0)
        cum = dff[dff['year_added'].between(2008, yt)].groupby('year_added')['show_id'].count().cumsum()

        fig = Figure(figsize=(14, 5.5), dpi=92)
        fig.patch.set_facecolor(BG)

        ax1 = fig.add_subplot(121)
        if 'Movie' in yoy.columns:
            ax1.plot(yoy.index.astype(int), yoy['Movie'],   marker='o', color=RED,  label='Movies',   linewidth=2)
        if 'TV Show' in yoy.columns:
            ax1.plot(yoy.index.astype(int), yoy['TV Show'], marker='s', color=GOLD, label='TV Shows', linewidth=2)
        ax1.legend(facecolor=CARD, labelcolor=FG)
        style_ax(ax1, "Movies vs TV Shows Per Year")

        ax2 = fig.add_subplot(122)
        ax2.fill_between(cum.index.astype(int), cum.values, color=RED, alpha=0.22)
        ax2.plot(cum.index.astype(int), cum.values, color=RED, linewidth=2, marker='o')
        style_ax(ax2, "Cumulative Library Growth")

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=y5_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        y5_holder["canvas"] = canvas

    draw_yoy(df)
    yf_cb.bind("<<ComboboxSelected>>", lambda e: draw_yoy(df, int(yf_var.get()), int(yt_var.get())))
    yt_cb.bind("<<ComboboxSelected>>", lambda e: draw_yoy(df, int(yf_var.get()), int(yt_var.get())))

    # ══════════════════════════════════════════
    #  PAGE 6 — SEARCH & BROWSE
    # ══════════════════════════════════════════
    p6 = tk.Frame(nb, bg=BG)
    nb.add(p6, text="  Search & Browse  ")

    lbl(p6, "Search & Browse Titles", 18, bold=True).pack(anchor="w", padx=20, pady=(14,2))
    lbl(p6, "Search by title, director, or cast member — press Enter or click Search", 9, color=MUTED).pack(anchor="w", padx=20)

    s_ctrl = tk.Frame(p6, bg=BG)
    s_ctrl.pack(fill="x", padx=20, pady=8)

    search_var   = tk.StringVar()
    search_entry = tk.Entry(s_ctrl, textvariable=search_var, bg=CARD, fg=FG,
                            font=("Helvetica", 12), insertbackground=FG,
                            relief="flat", width=38)
    search_entry.pack(side="left", padx=(0,8), ipady=6, ipadx=8)

    sf_var = tk.StringVar(value="Title")
    sf_cb  = ttk.Combobox(s_ctrl, textvariable=sf_var, width=10,
                           values=["Title","Director","Cast","Genre"], state="readonly")
    sf_cb.pack(side="left", padx=4)

    search_btn = tk.Button(s_ctrl, text="  Search  ", bg=RED, fg=FG,
                            font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2")
    search_btn.pack(side="left", padx=6)

    result_lbl = lbl(s_ctrl, "", 9, color=MUTED, bg=BG)
    result_lbl.pack(side="left", padx=10)

    ts_style = ttk.Style()
    ts_style.configure("N.Treeview", background=CARD, foreground=FG, fieldbackground=CARD,
                       rowheight=28, font=("Helvetica",10))
    ts_style.configure("N.Treeview.Heading", background="#1F1F1F", foreground=RED,
                       font=("Helvetica",9,"bold"), relief="flat")
    ts_style.map("N.Treeview", background=[("selected", RED)])

    tree_frame = tk.Frame(p6, bg=CARD)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=8)

    cols = ("Title","Type","Country","Year Added","Rating","Duration","Genre")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                        style="N.Treeview", height=22)
    widths = [250, 80, 140, 80, 80, 90, 230]
    for col, w in zip(cols, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")

    sb_y = ttk.Scrollbar(tree_frame, orient="vertical",   command=tree.yview)
    sb_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
    sb_y.pack(side="right", fill="y")
    sb_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    def populate_tree(data):
        for row in tree.get_children():
            tree.delete(row)
        for _, r in data.head(300).iterrows():
            tree.insert("", "end", values=(
                r.get('title','—'),
                r.get('type','—'),
                r.get('primary_country','—'),
                int(r['year_added']) if pd.notna(r.get('year_added')) else '—',
                r.get('rating','—'),
                r.get('duration','—'),
                str(r.get('listed_in','—'))[:45],
            ))
        result_lbl.config(text=f"{len(data):,} results")

    populate_tree(df.sort_values('year_added', ascending=False))

    def do_search():
        q      = search_var.get().strip().lower()
        field  = sf_var.get()
        col_map= {"Title":"title","Director":"director","Cast":"cast","Genre":"listed_in"}
        col    = col_map[field]
        res    = df[df[col].str.lower().str.contains(q, na=False)] if q else df.sort_values('year_added', ascending=False)
        populate_tree(res)

    search_btn.config(command=do_search)
    search_entry.bind("<Return>", lambda e: do_search())

    # ══════════════════════════════════════════
    #  GLOBAL FILTER LOGIC
    # ══════════════════════════════════════════
    def get_filtered():
        dff = df.copy()
        if type_var.get()    != "All": dff = dff[dff['type']==type_var.get()]
        if country_var.get() != "All": dff = dff[dff['primary_country']==country_var.get()]
        if rating_var.get()  != "All": dff = dff[dff['rating']==rating_var.get()]
        try:
            dff = dff[dff['year_added'].between(int(yr_from.get()), int(yr_to.get()))]
        except Exception:
            pass
        return dff

    def apply_filters():
        dff   = get_filtered()
        parts = [v.get() for v in (type_var, country_var, rating_var) if v.get() != "All"]
        parts.append(f"{yr_from.get()}–{yr_to.get()}")
        filter_status.config(text=f"Showing: {len(dff):,} titles  |  " + ", ".join(parts))
        draw_overview(dff)
        draw_genre(dff, seg_var.get())
        draw_country(dff, sort_var.get(), int(rows_var.get()))
        draw_duration(dff, int(bins_var.get()))
        draw_yoy(dff, int(yf_var.get()), int(yt_var.get()))
        populate_tree(dff.sort_values('year_added', ascending=False))

    def reset_filters():
        type_var.set("All"); country_var.set("All")
        rating_var.set("All"); yr_from.set("2015"); yr_to.set("2021")
        filter_status.config(text="Showing: All data")
        draw_overview(df); draw_genre(df); draw_country(df)
        draw_duration(df); draw_yoy(df)
        populate_tree(df.sort_values('year_added', ascending=False))

    apply_btn.config(command=apply_filters)
    reset_btn.config(command=reset_filters)

    # ══════════════════════════════════════════
    #  PAGE 7 — TMDB LIVE DATA
    # ══════════════════════════════════════════
    p7 = tk.Frame(nb, bg=BG)
    nb.add(p7, text="  🌐 Live TMDB Data  ")

    TMDB_BASE = "https://api.themoviedb.org/3"

    api_row = tk.Frame(p7, bg="#0A0A0A", pady=8)
    api_row.pack(fill="x", padx=14, pady=(10, 0))

    lbl(api_row, "🔑 TMDB API Key:", 10, bold=True, color=GOLD, bg="#0A0A0A").pack(side="left", padx=(6,6))
    api_key_var = tk.StringVar()
    api_entry = tk.Entry(api_row, textvariable=api_key_var, bg=CARD, fg=FG,
                         font=("Helvetica", 11), insertbackground=FG,
                         relief="flat", width=38, show="*")
    api_entry.pack(side="left", ipady=5, ipadx=6)

    show_key_var = tk.BooleanVar(value=False)
    def toggle_key():
        api_entry.config(show="" if show_key_var.get() else "*")
    tk.Checkbutton(api_row, text="Show", variable=show_key_var, command=toggle_key,
                   bg="#0A0A0A", fg=MUTED, selectcolor=CARD,
                   font=("Helvetica", 9), relief="flat").pack(side="left", padx=6)

    lbl(api_row, "Get free key → themoviedb.org/settings/api", 9, color=MUTED, bg="#0A0A0A").pack(side="left", padx=10)

    api_status = lbl(api_row, "", 9, color=GOOD, bg="#0A0A0A")
    api_status.pack(side="right", padx=10)

    tmdb_nb_style = ttk.Style()
    tmdb_nb_style.configure("TMDB.TNotebook",     background=BG, borderwidth=0)
    tmdb_nb_style.configure("TMDB.TNotebook.Tab", background="#222", foreground=MUTED,
                            padding=(14, 7), font=("Helvetica", 9, "bold"))
    tmdb_nb_style.map("TMDB.TNotebook.Tab",       background=[("selected","#333")],
                      foreground=[("selected", GOLD)])

    tmdb_nb = ttk.Notebook(p7, style="TMDB.TNotebook")
    tmdb_nb.pack(fill="both", expand=True, padx=14, pady=8)

    # ─── Sub-tab A: Search ────────────────────
    ta = tk.Frame(tmdb_nb, bg=BG)
    tmdb_nb.add(ta, text=" Search Title ")

    lbl(ta, "Search any Movie or TV Show on TMDB", 14, bold=True).pack(anchor="w", padx=16, pady=(12,2))
    lbl(ta, "Fetches live rating, overview, genres, release date and popularity score", 9, color=MUTED).pack(anchor="w", padx=16)

    s_row = tk.Frame(ta, bg=BG)
    s_row.pack(fill="x", padx=16, pady=8)
    tmdb_q_var = tk.StringVar()
    tmdb_entry = tk.Entry(s_row, textvariable=tmdb_q_var, bg=CARD, fg=FG,
                          font=("Helvetica", 12), insertbackground=FG,
                          relief="flat", width=34)
    tmdb_entry.pack(side="left", ipady=6, ipadx=8)
    tmdb_type_var = tk.StringVar(value="Movie")
    ttk.Combobox(s_row, textvariable=tmdb_type_var, width=10,
                 values=["Movie", "TV Show"], state="readonly").pack(side="left", padx=6)
    tmdb_search_btn = tk.Button(s_row, text="  Fetch Live  ", bg=RED, fg=FG,
                                font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2")
    tmdb_search_btn.pack(side="left", padx=6)
    tmdb_spin_lbl = lbl(s_row, "", 10, color=GOLD, bg=BG)
    tmdb_spin_lbl.pack(side="left", padx=8)

    result_outer = tk.Frame(ta, bg=BG)
    result_outer.pack(fill="both", expand=True, padx=16, pady=6)

    result_card = tk.Frame(result_outer, bg=CARD, padx=20, pady=20)
    result_card.pack(side="left", fill="both", expand=True)

    rc_title   = lbl(result_card, "Enter a title and click  Fetch Live", 16, bold=True, color=MUTED, bg=CARD)
    rc_title.pack(anchor="w", pady=(0,8))
    rc_meta    = lbl(result_card, "", 10, color=MUTED, bg=CARD)
    rc_meta.pack(anchor="w")
    rc_rating  = lbl(result_card, "", 24, bold=True, color=GOLD, bg=CARD)
    rc_rating.pack(anchor="w", pady=4)
    rc_pop     = lbl(result_card, "", 10, color=GOOD, bg=CARD)
    rc_pop.pack(anchor="w")
    rc_genres  = lbl(result_card, "", 10, color="#00BFFF", bg=CARD)
    rc_genres.pack(anchor="w", pady=4)
    tk.Frame(result_card, bg="#2A2A2A", height=1).pack(fill="x", pady=8)
    rc_overview= tk.Text(result_card, bg=CARD, fg=FG, font=("Helvetica",10),
                         relief="flat", wrap="word", height=6, state="disabled")
    rc_overview.pack(fill="x")

    similar_frame = tk.Frame(result_outer, bg=CARD, padx=14, pady=14, width=260)
    similar_frame.pack(side="left", fill="y", padx=(10,0))
    similar_frame.pack_propagate(False)
    lbl(similar_frame, "Similar Titles", 11, bold=True, color=GOLD, bg=CARD).pack(anchor="w", pady=(0,8))
    similar_list_frame = tk.Frame(similar_frame, bg=CARD)
    similar_list_frame.pack(fill="both", expand=True)
    similar_labels = []
    for _ in range(8):
        sl = lbl(similar_list_frame, "", 9, color=MUTED, bg=CARD)
        sl.pack(anchor="w", pady=3)
        similar_labels.append(sl)

    def do_tmdb_search():
        key = api_key_var.get().strip()
        q   = tmdb_q_var.get().strip()
        if not key:
            api_status.config(text="⚠ Enter API key first", fg=WARN)
            return
        if not q:
            return
        tmdb_search_btn.config(state="disabled")
        tmdb_spin_lbl.config(text="⏳ Fetching...")

        def fetch():
            try:
                media = "tv" if tmdb_type_var.get() == "TV Show" else "movie"
                r = requests.get(f"{TMDB_BASE}/search/{media}",
                                 params={"api_key": key, "query": q}, timeout=8)
                if r.status_code == 401:
                    root.after(0, lambda: api_status.config(text="❌ Invalid API key", fg=WARN))
                    return
                r.raise_for_status()
                results = r.json().get("results", [])
                if not results:
                    root.after(0, lambda: rc_title.config(text="No results found.", fg=WARN))
                    return

                item    = results[0]
                item_id = item["id"]
                title   = item.get("title") or item.get("name","—")
                rating  = item.get("vote_average", 0)
                votes   = item.get("vote_count", 0)
                pop     = item.get("popularity", 0)
                overview= item.get("overview","No overview available.")
                date    = item.get("release_date") or item.get("first_air_date","—")
                fetched_at = datetime.now().strftime("%H:%M:%S")

                det = requests.get(f"{TMDB_BASE}/{media}/{item_id}",
                                   params={"api_key": key}, timeout=8).json()
                genres  = ", ".join(g["name"] for g in det.get("genres",[]))
                lang    = det.get("original_language","—").upper()
                runtime = det.get("runtime") or (det.get("episode_run_time") or [None])[0]

                sim = requests.get(f"{TMDB_BASE}/{media}/{item_id}/similar",
                                   params={"api_key": key}, timeout=8).json()
                sim_titles = [s.get("title") or s.get("name","") for s in sim.get("results",[])[:8]]

                root.after(0, lambda: update_card(title, rating, votes, pop, overview,
                                                  date, genres, lang, runtime,
                                                  sim_titles, fetched_at))
                root.after(0, lambda: api_status.config(
                    text=f"✅ Live data fetched at {fetched_at}", fg=GOOD))
            except Exception as e:
                root.after(0, lambda: api_status.config(text=f"❌ Error: {e}", fg=WARN))
            finally:
                root.after(0, lambda: tmdb_search_btn.config(state="normal"))
                root.after(0, lambda: tmdb_spin_lbl.config(text=""))

        threading.Thread(target=fetch, daemon=True).start()

    def update_card(title, rating, votes, pop, overview, date, genres, lang, runtime, sim_titles, ts):
        rc_title.config(text=title, fg=FG)
        meta = f"Released: {date}   |   Language: {lang}"
        if runtime:
            meta += f"   |   Runtime: {runtime} min"
        rc_meta.config(text=meta)
        stars = "★" * int(rating/2) + "☆" * (5 - int(rating/2))
        rc_rating.config(text=f"{rating:.1f} / 10   {stars}   ({votes:,} votes)")
        rc_pop.config(text=f"Popularity Score: {pop:.1f}   •   Last updated: {ts}")
        rc_genres.config(text=f"Genres: {genres}")
        rc_overview.config(state="normal")
        rc_overview.delete("1.0","end")
        rc_overview.insert("1.0", overview)
        rc_overview.config(state="disabled")
        for i, sl in enumerate(similar_labels):
            sl.config(text=f"• {sim_titles[i]}" if i < len(sim_titles) else "", fg=FG)

    tmdb_search_btn.config(command=do_tmdb_search)
    tmdb_entry.bind("<Return>", lambda e: do_tmdb_search())

    # ─── Sub-tab B: Trending Now ──────────────
    tb = tk.Frame(tmdb_nb, bg=BG)
    tmdb_nb.add(tb, text=" Trending Now ")

    lbl(tb, "Live Trending Movies & TV Shows", 14, bold=True).pack(anchor="w", padx=16, pady=(12,2))
    lbl(tb, "Fetched in real-time from TMDB — updates every time you click Refresh", 9, color=MUTED).pack(anchor="w", padx=16)

    trend_ctrl = tk.Frame(tb, bg=BG)
    trend_ctrl.pack(fill="x", padx=16, pady=8)
    trend_type_var   = tk.StringVar(value="movie")
    trend_window_var = tk.StringVar(value="week")
    ttk.Combobox(trend_ctrl, textvariable=trend_type_var, width=10,
                 values=["movie","tv"], state="readonly").pack(side="left", padx=(0,8))
    ttk.Combobox(trend_ctrl, textvariable=trend_window_var, width=8,
                 values=["day","week"], state="readonly").pack(side="left", padx=(0,8))
    trend_btn = tk.Button(trend_ctrl, text="  Refresh Trending  ", bg=RED, fg=FG,
                          font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2")
    trend_btn.pack(side="left")
    trend_spin = lbl(trend_ctrl, "", 10, color=GOLD, bg=BG)
    trend_spin.pack(side="left", padx=10)
    trend_ts = lbl(trend_ctrl, "", 9, color=MUTED, bg=BG)
    trend_ts.pack(side="right", padx=10)

    trend_main = tk.Frame(tb, bg=BG)
    trend_main.pack(fill="both", expand=True, padx=16, pady=4)

    trend_tbl_frame = tk.Frame(trend_main, bg=CARD)
    trend_tbl_frame.pack(side="left", fill="both", expand=True, padx=(0,10))

    tr_cols = ("#", "Title", "Rating", "Popularity", "Release Date", "Language")
    trend_tree = ttk.Treeview(trend_tbl_frame, columns=tr_cols, show="headings",
                               style="N.Treeview", height=16)
    tr_widths  = [35, 240, 70, 90, 100, 70]
    for col, w in zip(tr_cols, tr_widths):
        trend_tree.heading(col, text=col)
        trend_tree.column(col, width=w, anchor="w")
    trend_tree.pack(fill="both", expand=True, padx=8, pady=8)

    trend_chart_frame = tk.Frame(trend_main, bg=CARD, width=280)
    trend_chart_frame.pack(side="left", fill="y")
    trend_chart_frame.pack_propagate(False)
    trend_chart_holder = {"canvas": None}

    def draw_trend_chart(titles, ratings):
        if trend_chart_holder["canvas"]:
            trend_chart_holder["canvas"].get_tk_widget().destroy()
        fig = Figure(figsize=(3.2, 5.5), dpi=90)
        fig.patch.set_facecolor(CARD)
        ax  = fig.add_subplot(111)
        ax.set_facecolor(CARD)
        short = [t[:18]+"…" if len(t)>18 else t for t in titles[:10]]
        clrs  = [RED if r >= 7.5 else GOLD if r >= 6 else MUTED for r in ratings[:10]]
        ax.barh(short[::-1], ratings[:10][::-1], color=clrs[::-1], edgecolor="none")
        ax.set_xlim(0, 10)
        ax.set_title("Rating Comparison", color=FG, fontsize=9)
        ax.tick_params(colors=FG, labelsize=7)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.axvline(7, color=GOLD, linewidth=0.8, linestyle="--", alpha=0.5)
        fig.tight_layout(pad=1.5)
        canvas = FigureCanvasTkAgg(fig, master=trend_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        trend_chart_holder["canvas"] = canvas

    def fetch_trending():
        key = api_key_var.get().strip()
        if not key:
            api_status.config(text="⚠ Enter API key first", fg=WARN)
            return
        trend_btn.config(state="disabled")
        trend_spin.config(text="⏳ Fetching live data...")

        def fetch():
            try:
                media  = trend_type_var.get()
                window = trend_window_var.get()
                r = requests.get(f"{TMDB_BASE}/trending/{media}/{window}",
                                 params={"api_key": key}, timeout=8)
                r.raise_for_status()
                items = r.json().get("results", [])
                ts    = datetime.now().strftime("%d %b %Y  %H:%M:%S")

                def update():
                    for row in trend_tree.get_children():
                        trend_tree.delete(row)
                    titles  = []
                    ratings = []
                    for i, item in enumerate(items[:20], 1):
                        title  = item.get("title") or item.get("name","—")
                        rating = item.get("vote_average", 0)
                        pop    = item.get("popularity", 0)
                        date   = item.get("release_date") or item.get("first_air_date","—")
                        lang   = item.get("original_language","—").upper()
                        trend_tree.insert("","end",
                            values=(i, title, f"{rating:.1f}⭐", f"{pop:.0f}", date, lang))
                        titles.append(title)
                        ratings.append(rating)
                    draw_trend_chart(titles, ratings)
                    trend_ts.config(text=f"Live data — fetched at {ts}")
                    api_status.config(text=f"✅ Trending data fetched at {ts}", fg=GOOD)

                root.after(0, update)
            except Exception as e:
                root.after(0, lambda: api_status.config(text=f"❌ Error: {e}", fg=WARN))
            finally:
                root.after(0, lambda: trend_btn.config(state="normal"))
                root.after(0, lambda: trend_spin.config(text=""))

        threading.Thread(target=fetch, daemon=True).start()

    trend_btn.config(command=fetch_trending)

    # ─── Sub-tab C: Top Rated ─────────────────
    tc = tk.Frame(tmdb_nb, bg=BG)
    tmdb_nb.add(tc, text=" Top Rated ")

    lbl(tc, "Top Rated Titles from TMDB", 14, bold=True).pack(anchor="w", padx=16, pady=(12,2))
    lbl(tc, "Live top-rated movies or TV shows with ratings, votes and genres", 9, color=MUTED).pack(anchor="w", padx=16)

    topr_ctrl = tk.Frame(tc, bg=BG)
    topr_ctrl.pack(fill="x", padx=16, pady=8)
    topr_type = tk.StringVar(value="movie")
    ttk.Combobox(topr_ctrl, textvariable=topr_type, width=10,
                 values=["movie","tv"], state="readonly").pack(side="left", padx=(0,8))
    topr_btn = tk.Button(topr_ctrl, text="  Fetch Top Rated  ", bg=RED, fg=FG,
                         font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2")
    topr_btn.pack(side="left")
    topr_spin = lbl(topr_ctrl, "", 10, color=GOLD, bg=BG)
    topr_spin.pack(side="left", padx=10)
    topr_ts = lbl(topr_ctrl, "", 9, color=MUTED, bg=BG)
    topr_ts.pack(side="right", padx=10)

    topr_main = tk.Frame(tc, bg=BG)
    topr_main.pack(fill="both", expand=True, padx=16, pady=4)

    topr_tbl = tk.Frame(topr_main, bg=CARD)
    topr_tbl.pack(side="left", fill="both", expand=True, padx=(0,10))
    topr_cols = ("#","Title","Rating","Votes","Popularity","Language")
    topr_tree = ttk.Treeview(topr_tbl, columns=topr_cols, show="headings",
                              style="N.Treeview", height=16)
    topr_ws = [35,250,75,100,100,75]
    for col,w in zip(topr_cols,topr_ws):
        topr_tree.heading(col,text=col)
        topr_tree.column(col,width=w,anchor="w")
    topr_tree.pack(fill="both",expand=True,padx=8,pady=8)

    topr_chart_frame = tk.Frame(topr_main, bg=CARD, width=280)
    topr_chart_frame.pack(side="left", fill="y")
    topr_chart_frame.pack_propagate(False)
    topr_chart_holder = {"canvas": None}

    def fetch_top_rated():
        key = api_key_var.get().strip()
        if not key:
            api_status.config(text="⚠ Enter API key first", fg=WARN)
            return
        topr_btn.config(state="disabled")
        topr_spin.config(text="⏳ Fetching...")

        def fetch():
            try:
                media = topr_type.get()
                r = requests.get(f"{TMDB_BASE}/{media}/top_rated",
                                 params={"api_key": key, "page": 1}, timeout=8)
                r.raise_for_status()
                items = r.json().get("results", [])
                ts    = datetime.now().strftime("%d %b %Y  %H:%M:%S")

                def update():
                    for row in topr_tree.get_children():
                        topr_tree.delete(row)
                    titles, ratings, votes_list = [], [], []
                    for i, item in enumerate(items[:20], 1):
                        title  = item.get("title") or item.get("name","—")
                        rating = item.get("vote_average",0)
                        votes  = item.get("vote_count",0)
                        pop    = item.get("popularity",0)
                        lang   = item.get("original_language","—").upper()
                        topr_tree.insert("","end",
                            values=(i,title,f"{rating:.1f}⭐",f"{votes:,}",f"{pop:.0f}",lang))
                        titles.append(title); ratings.append(rating); votes_list.append(votes)
                    if topr_chart_holder["canvas"]:
                        topr_chart_holder["canvas"].get_tk_widget().destroy()
                    fig = Figure(figsize=(3.2,5.5), dpi=90)
                    fig.patch.set_facecolor(CARD)
                    ax  = fig.add_subplot(111)
                    ax.set_facecolor(CARD)
                    short = [t[:16]+"…" if len(t)>16 else t for t in titles[:10]]
                    ax.barh(short[::-1], [v/1000 for v in votes_list[:10][::-1]],
                            color=GOLD, edgecolor="none")
                    ax.set_title("Vote Count (thousands)", color=FG, fontsize=9)
                    ax.tick_params(colors=FG, labelsize=7)
                    for sp in ax.spines.values(): sp.set_visible(False)
                    fig.tight_layout(pad=1.5)
                    canvas = FigureCanvasTkAgg(fig, master=topr_chart_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both",expand=True,padx=6,pady=6)
                    topr_chart_holder["canvas"] = canvas
                    topr_ts.config(text=f"Fetched at {ts}")
                    api_status.config(text=f"✅ Top Rated fetched at {ts}", fg=GOOD)

                root.after(0, update)
            except Exception as e:
                root.after(0, lambda: api_status.config(text=f"❌ Error: {e}", fg=WARN))
            finally:
                root.after(0, lambda: topr_btn.config(state="normal"))
                root.after(0, lambda: topr_spin.config(text=""))

        threading.Thread(target=fetch, daemon=True).start()

    topr_btn.config(command=fetch_top_rated)

    # ══════════════════════════════════════════
    #  TAB CHANGE — hide filter bar on TMDB tab
    # ══════════════════════════════════════════
    def on_tab_change(event):
        selected = nb.index(nb.select())
        if selected == 6:  # Live TMDB Data tab (0-indexed)
            fbar.pack_forget()
        else:
            if not fbar.winfo_ismapped():
                fbar.pack_forget()
                nb.pack_forget()
                header.pack_forget()

                header.pack(fill="x", padx=20, pady=(10, 4))
                fbar.pack(fill="x", padx=10, pady=(0, 4))
                nb.pack(fill="both", expand=True, padx=10, pady=6)

    nb.bind("<<NotebookTabChanged>>", on_tab_change)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(FILE_PATH):
        print(f"ERROR: '{FILE_PATH}' not found.")
        print("Download from: https://www.kaggle.com/datasets/shivamb/netflix-shows")
        exit(1)
    df   = load_data()
    root = tk.Tk()
    build_dashboard(root, df)
    root.mainloop()