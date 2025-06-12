import streamlit as st
import pandas as pd
import re
import unicodedata
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="Ferramenta de Limpeza de Dados",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DataCleaner:
    def __init__(self):
        self.df = None
        self.space_chars = r'[.,;:!?@#$%^&*_+=|\\/<>\[\]{}()\-"\'`~]'
        
        # Configurações padrão
        if 'to_lowercase' not in st.session_state:
            st.session_state.to_lowercase = True
        if 'remove_special' not in st.session_state:
            st.session_state.remove_special = True

    def remove_accents(self, text):
        """Remove acentos e caracteres especiais de um texto"""
        text = unicodedata.normalize('NFKD', str(text))
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.replace('ç', 'c').replace('Ç', 'C')

    def separate_num_letter(self, text):
        """Adiciona espaço entre números e letras"""
        text = re.sub(r'(?<=\d)(?=[a-zA-Z])', ' ', str(text))
        text = re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ', text)
        return text

    def clean_dataframe(self):
        """Processa o dataframe com as configurações selecionadas"""
        if self.df is None:
            st.warning("Nenhum arquivo carregado")
            return None

        cleaned_df = self.df.copy()
        progress_bar = st.progress(0)
        total_cols = len(cleaned_df.columns)

        for i, col in enumerate(cleaned_df.columns):
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].astype(str)

                if st.session_state.to_lowercase:
                    cleaned_df[col] = cleaned_df[col].str.lower()

                if st.session_state.remove_special:
                    cleaned_df[col] = cleaned_df[col].apply(self.remove_accents)
                    cleaned_df[col] = cleaned_df[col].apply(
                        lambda x: re.sub(self.space_chars, ' ', x)
                    )

                cleaned_df[col] = cleaned_df[col].apply(self.separate_num_letter)
                cleaned_df[col] = cleaned_df[col].str.replace(r'\s+', ' ', regex=True).str.strip()

            progress_bar.progress((i + 1) / total_cols)

        progress_bar.empty()
        return cleaned_df

    def to_excel(self, df):
        """Converte o dataframe para Excel em memória"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

def main():
    st.title("🧹 Ferramenta de Limpeza de Dados")
    cleaner = DataCleaner()

    # Sidebar com configurações
    with st.sidebar:
        st.header("⚙️ Configurações")

        st.session_state.to_lowercase = st.checkbox(
            "Converter texto para minúsculo",
            value=st.session_state.to_lowercase
        )

        st.session_state.remove_special = st.checkbox(
            "Remover caracteres especiais e acentos",
            value=st.session_state.remove_special
        )

        cleaner.space_chars = st.text_input(
            "Caracteres para substituir por espaço:",
            value=cleaner.space_chars
        )

    # Seção principal
    tab1, tab2 = st.tabs(["📤 Carregar Arquivo", "📊 Visualizar Dados"])

    with tab1:
        st.header("Carregar Arquivo Excel")
        uploaded_file = st.file_uploader(
            "Selecione o arquivo Excel",
            type=["xlsx", "xls"],
            key="file_uploader"
        )

        if uploaded_file:
            try:
                cleaner.df = pd.read_excel(uploaded_file)
                st.session_state.original_df = cleaner.df.copy()
                st.success(f"✅ Arquivo carregado com sucesso! ({len(cleaner.df)} registros)")
                st.subheader("Pré-visualização dos dados originais")
                st.dataframe(cleaner.df.head())
            except Exception as e:
                st.error(f"Erro ao carregar arquivo: {str(e)}")

    with tab2:
        if 'original_df' in st.session_state:
            cleaner.df = st.session_state.original_df
            st.header("Dados Processados")

            if st.button("Processar Dados", type="primary"):
                with st.spinner("Processando dados..."):
                    cleaned_df = cleaner.clean_dataframe()
                    if cleaned_df is not None:
                        st.session_state.cleaned_df = cleaned_df
                        st.success("Processamento concluído!")
                        st.rerun()

        if 'cleaned_df' in st.session_state and st.session_state.cleaned_df is not None:
            st.subheader("Resultado do Processamento")
            st.dataframe(st.session_state.cleaned_df.head())

            # Container para o botão de download
            with st.container():
                st.markdown("---")
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    st.download_button(
                        label="⬇️ BAIXAR DADOS TRATADOS (Excel)",
                        data=cleaner.to_excel(st.session_state.cleaned_df),
                        file_name="dados_processados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary"
                    )
                st.markdown("---")
            
            # Visualização expandida
            with st.expander("🔍 Visualizar mais dados processados"):
                st.dataframe(st.session_state.cleaned_df)
        else:
            st.warning("Nenhum dado processado disponível. Carregue e processe um arquivo.")

if __name__ == "__main__":
    main()
