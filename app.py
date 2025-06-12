import streamlit as st
import pandas as pd
import re
import unicodedata
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="🧹 Ferramenta de Limpeza de Dados",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DataCleaner:
    def __init__(self):
        self.df = None
        self.space_chars = r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~]'

        # Configuração de estado da sessão
        st.session_state.setdefault('to_lowercase', True)
        st.session_state.setdefault('remove_special', True)
        st.session_state.setdefault('remove_extra_spaces', True)
        st.session_state.setdefault('separate_num_letter', True)

    def remove_accents(self, text):
        """Remove acentos e converte ç/Ç para c/C"""
        if pd.isna(text):
            return text
        text = str(text)
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.replace('ç', 'c').replace('Ç', 'C')

    def separate_num_letter(self, text):
        """Adiciona espaço entre números e letras"""
        if pd.isna(text):
            return text
        text = str(text)
        text = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', text)
        text = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', text)
        return text

    def clean_dataframe(self):
        """Processa o DataFrame com as configurações selecionadas"""
        if self.df is None or self.df.empty:
            st.warning("Nenhum arquivo carregado ou o arquivo está vazio.")
            return None

        cleaned_df = self.df.copy()
        progress_bar = st.progress(0)
        total_cols = len(cleaned_df.columns)

        for i, col in enumerate(cleaned_df.columns):
            # Converter para string apenas se não for numérico ou datetime
            if pd.api.types.is_string_dtype(cleaned_df[col]) or pd.api.types.is_object_dtype(cleaned_df[col]):
                cleaned_df[col] = cleaned_df[col].astype(str)

                if st.session_state.to_lowercase:
                    cleaned_df[col] = cleaned_df[col].str.lower()

                if st.session_state.remove_special:
                    cleaned_df[col] = cleaned_df[col].apply(self.remove_accents)
                    cleaned_df[col] = cleaned_df[col].apply(
                        lambda x: re.sub(self.space_chars, ' ', str(x)) if pd.notna(x) else x
                    )

                if st.session_state.separate_num_letter:
                    cleaned_df[col] = cleaned_df[col].apply(self.separate_num_letter)

                if st.session_state.remove_extra_spaces:
                    cleaned_df[col] = cleaned_df[col].str.replace(r'\s+', ' ', regex=True).str.strip()

            progress_bar.progress((i + 1) / total_cols)

        progress_bar.empty()
        return cleaned_df

    def to_excel(self, df):
        """Converte o DataFrame para um arquivo Excel em memória"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        processed_data = output.getvalue()
        return processed_data

def main():
    st.title("🧹 Ferramenta de Limpeza de Dados")
    cleaner = DataCleaner()

    # Sidebar – configurações
    with st.sidebar:
        st.header("⚙️ Configurações de Limpeza")

        st.session_state.to_lowercase = st.checkbox(
            "Converter texto para minúsculo",
            value=st.session_state.to_lowercase,
            help="Converte todo o texto para letras minúsculas"
        )

        st.session_state.remove_special = st.checkbox(
            "Remover caracteres especiais e acentos",
            value=st.session_state.remove_special,
            help="Remove acentos e caracteres especiais, substituindo por espaços"
        )

        st.session_state.separate_num_letter = st.checkbox(
            "Separar números de letras",
            value=st.session_state.separate_num_letter,
            help="Adiciona espaço entre números e letras (ex: ABC123 vira ABC 123)"
        )

        st.session_state.remove_extra_spaces = st.checkbox(
            "Remover espaços extras",
            value=st.session_state.remove_extra_spaces,
            help="Remove múltiplos espaços e espaços no início/fim"
        )

        cleaner.space_chars = st.text_input(
            "Caracteres a substituir por espaço:",
            value=cleaner.space_chars,
            help="Expressão regular dos caracteres que serão substituídos por espaços"
        )

    # Tabs – upload e visualização
    tab1, tab2 = st.tabs(["📤 Carregar Arquivo", "📊 Visualizar Dados"])

    with tab1:
        st.header("Upload de Arquivo Excel")
        uploaded_file = st.file_uploader(
            "Selecione um arquivo Excel (.xlsx ou .xls)",
            type=["xlsx", "xls"],
            accept_multiple_files=False
        )

        if uploaded_file is not None:
            try:
                cleaner.df = pd.read_excel(uploaded_file)
                if cleaner.df.empty:
                    st.warning("O arquivo está vazio.")
                else:
                    st.session_state.original_df = cleaner.df.copy()
                    st.success(f"✅ Arquivo carregado com sucesso ({len(cleaner.df)} registros, {len(cleaner.df.columns)} colunas).")
                    st.subheader("Pré-visualização dos dados")
                    st.dataframe(cleaner.df.head())
            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {str(e)}")

    with tab2:
        if 'original_df' in st.session_state and st.session_state.original_df is not None:
            cleaner.df = st.session_state.original_df.copy()
            st.header("Dados Processados")

            if st.button("🔄 Processar Dados", type="primary", use_container_width=True):
                with st.spinner("Processando dados..."):
                    cleaned_df = cleaner.clean_dataframe()
                    if cleaned_df is not None:
                        st.session_state.cleaned_df = cleaned_df
                        st.success("✅ Processamento concluído!")
                        st.rerun()

            if 'cleaned_df' in st.session_state and st.session_state.cleaned_df is not None:
                st.subheader("Resultado do Processamento")
                st.dataframe(st.session_state.cleaned_df.head())

                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="⬇️ Baixar dados tratados (Excel)",
                        data=cleaner.to_excel(st.session_state.cleaned_df),
                        file_name="dados_processados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                st.markdown("---")

                with st.expander("🔍 Visualizar mais dados"):
                    st.dataframe(st.session_state.cleaned_df)
            else:
                st.info("Clique em 'Processar Dados' para visualizar o resultado.")
        else:
            st.warning("Nenhum arquivo carregado. Por favor, carregue um arquivo na aba 'Carregar Arquivo'.")

if __name__ == "__main__":
    main()
