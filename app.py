import streamlit as st
import pandas as pd
import re
import unicodedata
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="🧹 Limpeza de Dados",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DataCleaner:
    def __init__(self):
        self.df = None
        self.space_chars = r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~]'

    def remove_accents(self, text):
        if pd.isna(text): return text
        text = str(text)
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.replace('ç', 'c').replace('Ç', 'C')

    def clean_dataframe(self, lowercase=True, remove_special=True):
        if self.df is None or self.df.empty:
            st.warning("⚠️ Carregue um arquivo Excel primeiro")
            return None

        cleaned_df = self.df.copy()
        for col in cleaned_df.columns:
            if pd.api.types.is_string_dtype(cleaned_df[col]):
                if lowercase: cleaned_df[col] = cleaned_df[col].str.lower()
                if remove_special:
                    cleaned_df[col] = cleaned_df[col].apply(self.remove_accents)
                    cleaned_df[col] = cleaned_df[col].str.replace(self.space_chars, ' ', regex=True)
                cleaned_df[col] = cleaned_df[col].str.replace(r'\s+', ' ', regex=True).str.strip()
        return cleaned_df

    def to_excel(self, df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

def main():
    st.title("🧹 Ferramenta de Limpeza de Dados")
    cleaner = DataCleaner()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        lowercase = st.checkbox("Converter para minúsculo", True)
        remove_special = st.checkbox("Remover caracteres especiais", True)
        cleaner.space_chars = st.text_input("Caracteres para remover:", cleaner.space_chars)

    # Upload
    uploaded_file = st.file_uploader("Carregue seu Excel", type=["xlsx", "xls"])
    if uploaded_file:
        cleaner.df = pd.read_excel(uploaded_file)
        st.success(f"✅ {len(cleaner.df)} registros carregados")

        if st.button("🔁 Processar Dados", type="primary"):
            with st.spinner("Processando..."):
                cleaned_df = cleaner.clean_dataframe(lowercase, remove_special)
                st.session_state.cleaned_df = cleaned_df
                st.rerun()

    # Resultado
    if 'cleaned_df' in st.session_state:
        st.dataframe(st.session_state.cleaned_df.head())
        st.download_button(
            "⬇️ Baixar Excel",
            cleaner.to_excel(st.session_state.cleaned_df),
            "dados_limpos.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
