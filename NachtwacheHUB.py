import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Nachtwache Los-System", layout="wide")

# Konfiguration
NIGHTS = ["Donnerstag", "Freitag", "Samstag"]
SLOTS = ["0-3", "3-6", "6-8"]
PERSONEN_PRO_SCHICHT = 2

# Initialisieren
if "data" not in st.session_state:
    st.session_state.data = {
        night: {
            "freiwillige": {slot: [] for slot in SLOTS},
            "zugeteilt": {slot: [] for slot in SLOTS},
            "offene_wuerfel": {}  # slot: person wartet auf Würfelentscheidung
        } for night in NIGHTS
    }

if "teilnehmer" not in st.session_state:
    st.session_state.teilnehmer = []

# Layout: Links Steuerung, rechts Übersicht
col_links, col_rechts = st.columns([1.5, 2])

# ----------------------------------
# 👈 Linke Seite: Steuerung
# ----------------------------------
with col_links:
    st.header("🛠️ Steuerung")

    # Teilnehmer hinzufügen (mit Enter)
    st.subheader("👤 Teilnehmer")
    with st.form(key="teilnehmer_form", clear_on_submit=True):
        name = st.text_input("Teilnehmer hinzufügen", placeholder="Name eingeben und Enter drücken")
        submitted = st.form_submit_button("➕ Hinzufügen")
        if submitted and name:
            if name not in st.session_state.teilnehmer:
                st.session_state.teilnehmer.append(name)
            else:
                st.warning("Teilnehmer existiert bereits.")

    st.write("**Alle Teilnehmer:**", st.session_state.teilnehmer)

    # Nacht/Slot-Auswahl
    st.subheader("🌙 Nachtwache planen")
    selected_night = st.selectbox("Nacht auswählen", NIGHTS)
    selected_slot = st.selectbox("Slot auswählen", SLOTS)

    data = st.session_state.data[selected_night]
    slot_key = f"{selected_night}_{selected_slot}"

    # Freiwillige melden
    st.markdown("**Freiwillige melden sich:**")
    moegliche_freiwillige = [
        p for p in st.session_state.teilnehmer
        if p not in data["freiwillige"][selected_slot] and p not in data["zugeteilt"][selected_slot]
    ]
    freiwillige_auswahl = st.multiselect("Freiwillige auswählen", moegliche_freiwillige, key=f"frei_{slot_key}")

    if st.button("✅ Eintragen"):
        for p in freiwillige_auswahl:
            if len(data["freiwillige"][selected_slot]) < PERSONEN_PRO_SCHICHT:
                data["freiwillige"][selected_slot].append(p)

    # Lostopf anzeigen
    bereits_verplant = set(sum(data["freiwillige"].values(), [])) | set(sum(data["zugeteilt"].values(), [])) | set(data["offene_wuerfel"].values())
    lostopf = [p for p in st.session_state.teilnehmer if p not in bereits_verplant]

    st.markdown("**🎩 Lostopf:**")
    st.write(lostopf)

    # Einzelnes Losen, falls nötig
    total_besetzt = len(data["freiwillige"][selected_slot]) + len(data["zugeteilt"][selected_slot])
    if total_besetzt < PERSONEN_PRO_SCHICHT:
        if st.button("🎲 1 Person losen"):
            if lostopf:
                gezogen = random.choice(lostopf)
                st.success(f"{gezogen} wurde gelost für Slot {selected_slot}")
                data["offene_wuerfel"][selected_slot] = gezogen
            else:
                st.warning("⚠️ Kein Teilnehmer mehr im Lostopf.")

    # Würfelentscheidung
    if selected_slot in data["offene_wuerfel"]:
        person = data["offene_wuerfel"][selected_slot]
        st.info(f"{person} wurde gelost für Slot {selected_slot}.")

        wahl_key = f"wahl_{slot_key}"
        wahl = st.radio(
            f"{person}, möchtest du würfeln?",
            ["Bitte wählen", "Nein", "Ja"],
            horizontal=True,
            key=wahl_key
        )

        if wahl == "Nein":
            data["zugeteilt"][selected_slot].append(person)
            del data["offene_wuerfel"][selected_slot]
            st.success(f"{person} übernimmt die Schicht ohne Würfeln.")

        elif wahl == "Ja":
            if f"wurf_ausgeloest_{slot_key}" not in st.session_state:
                if st.button("🎯 Jetzt würfeln!", key=f"btn_{slot_key}"):
                    st.session_state[f"wurf_ausgeloest_{slot_key}"] = True
                    st.session_state[f"wurf_wert_{slot_key}"] = random.randint(1, 6)

            if st.session_state.get(f"wurf_ausgeloest_{slot_key}"):
                wurf = st.session_state[f"wurf_wert_{slot_key}"]
                st.success(f"{person} hat eine **{wurf}** gewürfelt!")

                if wurf == 1:
                    st.info(f"{person} kommt **2× zurück** in den Lostopf.")
                    # Kein Eintrag nötig – Lostopf wird dynamisch berechnet
                elif wurf == 6:
                    st.info(f"{person} ist **komplett raus** aus der Nachtwache.")
                else:
                    st.info(f"{person} übernimmt die Schicht.")
                    if person not in data["zugeteilt"][selected_slot]:
                        data["zugeteilt"][selected_slot].append(person)

                # Aufräumen
                del data["offene_wuerfel"][selected_slot]
                del st.session_state[f"wurf_ausgeloest_{slot_key}"]
                del st.session_state[f"wurf_wert_{slot_key}"]

    st.divider()
    if st.button("🔁 Alles zurücksetzen"):
        st.session_state.clear()
        st.experimental_rerun()

# ----------------------------------
# 👉 Rechte Seite: Übersicht
# ----------------------------------
with col_rechts:
    st.header("📋 Nachtwachen-Übersicht")

    rows = []
    for night in NIGHTS:
        d = st.session_state.data[night]
        for slot in SLOTS:
            f = ", ".join(d["freiwillige"][slot]) if d["freiwillige"][slot] else "-"
            z = ", ".join(d["zugeteilt"][slot]) if d["zugeteilt"][slot] else "-"
            rows.append({
                "Nacht": night,
                "Slot": slot,
                "Freiwillige": f,
                "Gelost": z
            })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
