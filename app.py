import streamlit as st
import math
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Analisador Under/Over",
    page_icon="⚽",
    layout="wide"
)

class AnalisadorApostasUnderOver:
    def __init__(self):
        # Pontos de referência para curva padrão (Under ~39)
        self.pontos_referencia = {
            1: 1.0,      # 100% do valor inicial
            15: 0.67,    # 67% do valor inicial  
            30: 0.36,    # 36% do valor inicial
            45: 0.23,    # 23% do valor inicial
            46: 0.22,    # Início 2º tempo
            60: 0.15,    # 15% do valor inicial
            75: 0.08,    # 8% do valor inicial
            85: 0.05,    # 5% do valor inicial
            90: 0.04     # 4% do valor inicial (final)
        }
    
    def calcular_under_final_esperado(self, under_inicial):
        """Cálculo mais conservador do Under final"""
        if under_inicial >= 50:
            return max(1.50, under_inicial * 0.035)
        elif under_inicial >= 30:
            return max(1.40, under_inicial * 0.045)
        elif under_inicial >= 20:
            return max(1.30, under_inicial * 0.055)
        elif under_inicial >= 15:
            return max(1.25, under_inicial * 0.070)
        elif under_inicial >= 10:
            return max(1.20, under_inicial * 0.100)
        elif under_inicial >= 7:
            return max(1.15, under_inicial * 0.140)
        elif under_inicial >= 5:
            return max(1.10, under_inicial * 0.180)
        elif under_inicial >= 3:
            return max(1.05, under_inicial * 0.300)
        else:
            return max(1.03, under_inicial * 0.500)
    
    def calcular_over_baseado_no_under(self, under_atual):
        """Cálculo seguro do Over"""
        try:
            under_atual = max(under_atual, 1.01)
            prob_under = 1 / under_atual
            prob_over = 1 - prob_under
            
            if prob_over <= 0.01:
                return 15.0
            
            over_atual = 1 / prob_over
            return min(over_atual, 15.0)
        except:
            return 15.0
    
    def gerar_curva_monotonica(self, under_inicial, under_final):
        """NOVA: Gera curva estritamente decrescente"""
        curva_pontos = {}
        
        # Calcula valores para cada ponto de referência
        for minuto, percentual in self.pontos_referencia.items():
            if minuto == 90:
                valor = under_final
            else:
                # Interpolação entre inicial e final
                valor_bruto = under_inicial * percentual
                # Garante que nunca seja menor que o final
                valor = max(valor_bruto, under_final + (90 - minuto) * 0.001)
            
            curva_pontos[minuto] = valor
        
        # CRÍTICO: Garante monotonicidade decrescente
        minutos_ordenados = sorted(curva_pontos.keys())
        for i in range(1, len(minutos_ordenados)):
            minuto_atual = minutos_ordenados[i]
            minuto_anterior = minutos_ordenados[i-1]
            
            # Se o valor atual for maior que o anterior, ajusta
            if curva_pontos[minuto_atual] > curva_pontos[minuto_anterior]:
                curva_pontos[minuto_atual] = curva_pontos[minuto_anterior] * 0.99
        
        return curva_pontos
    
    def interpolar_suave(self, minuto, pontos_curva):
        """Interpolação que mantém monotonicidade"""
        if minuto in pontos_curva:
            return pontos_curva[minuto]
        
        minutos_ordenados = sorted(pontos_curva.keys())
        
        # Casos extremos
        if minuto <= minutos_ordenados[0]:
            return pontos_curva[minutos_ordenados[0]]
        if minuto >= minutos_ordenados[-1]:
            return pontos_curva[minutos_ordenados[-1]]
        
        # Encontra segmento para interpolação
        for i in range(len(minutos_ordenados) - 1):
            min1 = minutos_ordenados[i]
            min2 = minutos_ordenados[i + 1]
            
            if min1 <= minuto <= min2:
                val1 = pontos_curva[min1]
                val2 = pontos_curva[min2]
                
                # Interpolação linear
                fator = (minuto - min1) / (min2 - min1)
                valor = val1 + (val2 - val1) * fator
                
                # GARANTIA: Valor interpolado não pode ser maior que val1
                return min(valor, val1)
        
        return pontos_curva[minutos_ordenados[-1]]
    
    def gerar_curva_equilibrio_90min(self, under_inicial, over_inicial):
        """Gera curva completamente robusta"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Gera pontos de controle monotônicos
        pontos_curva = self.gerar_curva_monotonica(under_inicial, under_final)
        
        # Gera curva completa minuto a minuto
        curva = []
        valor_anterior = under_inicial
        
        for minuto in range(1, 91):
            under_atual = self.interpolar_suave(minuto, pontos_curva)
            
            # DUPLA VERIFICAÇÃO: Garante que nunca sobe
            under_atual = min(under_atual, valor_anterior)
            under_atual = max(under_atual, 1.01)  # Mínimo absoluto
            
            over_atual = self.calcular_over_baseado_no_under(under_atual)
            
            curva.append({
                'minuto': minuto,
                'under': round(under_atual, 2),
                'over': round(over_atual, 3)
            })
            
            valor_anterior = under_atual
        
        return curva
    
    def analisar_divergencia(self, under_atual_real, under_esperado, minuto):
        """Análise de divergência"""
        if under_esperado <= 0:
            under_esperado = 1.01
            
        divergencia_percent = ((under_atual_real - under_esperado) / under_esperado) * 100
        
        if divergencia_percent >= 15:
            status = "🔥 OPORTUNIDADE ALTA"
            explicacao = "Odd atual muito ACIMA da projetada"
            recomendacao = "✅ EXCELENTE momento para entrada Under"
            risco = "Baixo"
        elif divergencia_percent >= 8:
            status = "💰 OPORTUNIDADE MÉDIA"
            explicacao = "Odd atual ACIMA da projetada"
            recomendacao = "✅ Bom momento para entrada Under"
            risco = "Médio"
        elif divergencia_percent >= -8:
            status = "⚖️ EQUILIBRADO"
            explicacao = "Odd atual próxima da projetada"
            recomendacao = "⚠️ Entrada neutra"
            risco = "Médio"
        elif divergencia_percent >= -15:
            status = "⚠️ CUIDADO"
            explicacao = "Odd atual ABAIXO da projetada"
            recomendacao = "❌ Entrada Under arriscada"
            risco = "Alto"
        else:
            status = "🚨 RISCO ALTO"
            explicacao = "Odd atual muito ABAIXO da projetada"
            recomendacao = "❌ EVITAR entrada Under"
            risco = "Muito Alto"
        
        return {
            'status': status,
            'divergencia_percent': round(divergencia_percent, 1),
            'explicacao': explicacao,
            'recomendacao': recomendacao,
            'risco': risco
        }
    
    def calcular_taxa_queda(self, under_inicial, under_atual, minutos):
        if minutos == 0:
            return 0
        return (under_inicial - under_atual) / (under_inicial * minutos)
    
    def classificar_ritmo(self, taxa_queda):
        if taxa_queda >= 0.015:
            return "DESACELERADA ⏰", "Ritmo lento, partida conservadora"
        else:
            return "ACELERADA ⚡", "Ritmo rápido, partida ofensiva"
    
    def analisar_melhor_entrada_under(self, curva):
        melhores_entradas = []
        
        for i in range(10, 60, 5):  # Analisa a cada 5 minutos
            if i + 15 < len(curva):  # Janela de 15 minutos
                odd_entrada = curva[i]['under']
                odd_depois = curva[i + 15]['under']
                
                if odd_entrada > 1.20 and odd_depois > 1.05:
                    queda_percent = ((odd_entrada - odd_depois) / odd_entrada) * 100
                    
                    if queda_percent >= 10:  # Mínimo 10% de queda
                        melhores_entradas.append({
                            'minuto': i + 1,
                            'odd_entrada': odd_entrada,
                            'odd_apos_15min': odd_depois,
                            'queda_percent': round(queda_percent, 1),
                            'potencial_lucro': f"{queda_percent:.1f}%"
                        })
        
        return sorted(melhores_entradas, key=lambda x: x['queda_percent'], reverse=True)[:3]
    
    def analisar_melhor_entrada_over(self, curva):
        melhores_entradas = []
        
        for i in range(60, 85, 3):
            if i < len(curva):
                odd_over = curva[i]['over']
                
                if 1.5 <= odd_over <= 10.0:  # Range razoável
                    melhores_entradas.append({
                        'minuto': i + 1,
                        'odd_entrada': odd_over,
                        'estabilidade': 'Alta' if odd_over <= 5.0 else 'Média'
                    })
        
        return melhores_entradas[:3]
    
    def projetar_restante_equilibrio(self, under_inicial, under_atual, minuto_atual, placar):
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Cria curva do minuto atual até o final
        pontos_restantes = {}
        pontos_restantes[minuto_atual] = under_atual
        
        # Pontos intermediários até o final
        for min_futuro in range(minuto_atual + 5, 91, 5):
            if min_futuro == 90:
                pontos_restantes[min_futuro] = under_final
            else:
                # Progressão linear decrescente
                progresso = (min_futuro - minuto_atual) / (90 - minuto_atual)
                valor = under_atual + (under_final - under_atual) * progresso
                pontos_restantes[min_futuro] = max(valor, under_final)
        
        pontos_restantes[90] = under_final
        
        # Gera projeção minuto a minuto
        projecao = []
        for minuto in range(minuto_atual + 1, 91):
            under_proj = self.interpolar_suave(minuto, pontos_restantes)
            under_proj = max(under_proj, under_final)  # Nunca abaixo do final
            over_proj = self.calcular_over_baseado_no_under(under_proj)
            
            projecao.append({
                'minuto': minuto,
                'under': round(under_proj, 2),
                'over': round(over_proj, 3)
            })
        
        return projecao

# Interface Streamlit
st.title("🎯 Analisador Under/Over v4.0 - ROBUSTO")
st.subheader("🔄 Curva Estritamente Decrescente")

# Sidebar
st.sidebar.header("⚙️ Configurações")

modo = st.sidebar.selectbox(
    "📊 Selecione o Modo:",
    ["🎯 Jogo em Andamento", "📈 Projeção Completa"]
)

if modo == "📈 Projeção Completa":
    st.sidebar.subheader("📋 Dados Iniciais")
    under_inicial = st.sidebar.number_input("Under Inicial:", value=7.0, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial = st.sidebar.number_input("Over Inicial:", value=1.14, min_value=1.01, max_value=999.0, step=0.01)
    
    if st.sidebar.button("🚀 Executar Análise", type="primary"):
        analisador = AnalisadorApostasUnderOver()
        
        st.header("📊 Projeção Completa (90 Minutos)")
        
        # Cálculos
        under_final_calc = analisador.calcular_under_final_esperado(under_inicial)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Under Inicial", f"{under_inicial}")
            st.metric("Over Inicial", f"{over_inicial}")
            st.success("✅ **Garantia:** Curva SEMPRE decrescente")
        
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial, over_inicial)
        
        with col2:
            st.metric("Under Final", f"{curva[89]['under']}")
            st.metric("Over Final", f"{curva[89]['over']}")
            
            # Verificação de consistência
            under_min85 = curva[84]['under']  # Minuto 85
            under_final = curva[89]['under']   # Minuto 90
            
            if under_final <= under_min85:
                st.success("✅ Curva Consistente")
            else:
                st.error("❌ Erro na Curva")
        
        # Gráficos
        df_curva = pd.DataFrame(curva)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolução Under (Decrescente)")
            st.line_chart(df_curva.set_index('minuto')['under'])
        
        with col2:
            st.subheader("📈 Evolução Over")
            st.line_chart(df_curva.set_index('minuto')['over'])
        
        # Verificação matemática
        st.subheader("🔍 Verificação de Monotonicidade")
        
        # Verifica se a curva é sempre decrescente
        problemas = []
        for i in range(1, len(curva)):
            if curva[i]['under'] > curva[i-1]['under']:
                problemas.append(f"Min {curva[i]['minuto']}: {curva[i]['under']} > {curva[i-1]['under']}")
        
        if problemas:
            st.error(f"❌ **Problemas encontrados:** {len(problemas)}")
            for problema in problemas[:5]:  # Mostra até 5 problemas
                st.write(f"• {problema}")
        else:
            st.success("✅ **Perfeito!** Curva sempre decrescente ou estável")
        
        # Estratégias
        st.subheader("🎯 Estratégias de Entrada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("💎 **Melhores Entradas Under:**")
            melhores_under = analisador.analisar_melhor_entrada_under(curva)
            if melhores_under:
                for i, entrada in enumerate(melhores_under, 1):
                    st.write(f"{i}. Min {entrada['minuto']}: {entrada['odd_entrada']} → {entrada['odd_apos_15min']} ({entrada['potencial_lucro']})")
            else:
                st.write("❌ Nenhuma oportunidade Under identificada")
        
        with col2:
            st.write("🚀 **Entradas Over Seguras:**")
            melhores_over = analisador.analisar_melhor_entrada_over(curva)
            if melhores_over:
                for i, entrada in enumerate(melhores_over, 1):
                    st.write(f"{i}. Min {entrada['minuto']}: {entrada['odd_entrada']:.3f} ({entrada['estabilidade']})")
            else:
                st.write("❌ Nenhuma oportunidade Over identificada")
        
        # Tabela completa
        st.subheader("📊 Tabela Completa Minuto a Minuto")
        
        df_display = df_curva.copy()
        df_display['Minuto'] = df_display['minuto']
        df_display['Under'] = df_display['under']
        df_display['Over'] = df_display['over']
        df_display = df_display[['Minuto', 'Under', 'Over']]
        
        st.dataframe(df_display, use_container_width=True, height=400)

else:
    # Modo Jogo em Andamento
    st.sidebar.subheader("📋 Dados do Jogo")
    placar_atual = st.sidebar.text_input("Placar Atual:", value="0x1")
    under_inicial_jogo = st.sidebar.number_input("Under Inicial:", value=7.0, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial_jogo = st.sidebar.number_input("Over Inicial:", value=1.14, min_value=1.01, max_value=999.0, step=0.01)
    under_atual = st.sidebar.number_input("Under Atual:", value=5.0, min_value=1.01, max_value=999.0, step=0.1)
    over_atual = st.sidebar.number_input("Over Atual:", value=1.25, min_value=1.01, max_value=999.0, step=0.01)
    minuto_atual = st.sidebar.slider("Minuto Atual:", min_value=1, max_value=89, value=20)
    
    if st.sidebar.button("🚀 Executar Análise", type="primary"):
        analisador = AnalisadorApostasUnderOver()
        
        st.header("📊 Jogo em Andamento")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Placar", placar_atual)
            st.metric("Minuto", f"{minuto_atual}'")
        
        with col2:
            st.metric("Under", f"{under_inicial_jogo} → {under_atual}")
            
        with col3:
            st.metric("Over", f"{over_inicial_jogo} → {over_atual}")
        
        # Análise
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial_jogo, over_inicial_jogo)
        under_esperado = curva[minuto_atual - 1]['under']
        
        divergencia = analisador.analisar_divergencia(under_atual, under_esperado, minuto_atual)
        
        st.subheader("🔍 Análise de Divergência")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Under Esperado", f"{under_esperado:.2f}")
            st.metric("Under Atual", f"{under_atual}")
            st.metric("Divergência", f"{divergencia['divergencia_percent']:+.1f}%")
        
        with col2:
            st.write(f"**Status:** {divergencia['status']}")
            st.write(f"**Explicação:** {divergencia['explicacao']}")
            st.write(f"**Recomendação:** {divergencia['recomendacao']}")
            st.write(f"**Risco:** {divergencia['risco']}")
        
        # Ritmo
        taxa_queda = analisador.calcular_taxa_queda(under_inicial_jogo, under_atual, minuto_atual)
        ritmo, descricao = analisador.classificar_ritmo(taxa_queda)
        
        st.subheader("📊 Análise de Ritmo")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Taxa de Queda", f"{taxa_queda:.4f}/min")
            st.metric("Perfil", ritmo)
        
        with col2:
            st.write(f"**Descrição:** {descricao}")
        
        # Projeção final
        under_final = analisador.calcular_under_final_esperado(under_inicial_jogo)
        over_final = analisador.calcular_over_baseado_no_under(under_final)
        queda_restante = ((under_atual - under_final) / under_atual) * 100 if under_atual > under_final else 0
        
        st.subheader("🎯 Projeção Final")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Under Final", f"{under_final:.2f}")
        
        with col2:
            st.metric("Over Final", f"{over_final:.3f}")
        
        with col3:
            if queda_restante > 30:
                potencial = "🔥 MUITO ALTO"
            elif queda_restante > 20:
                potencial = "💰 ALTO"
            elif queda_restante > 10:
                potencial = "⚖️ MÉDIO"
            else:
                potencial = "⚠️ BAIXO"
            
            st.metric("Potencial Under", potencial)
            st.metric("Queda Restante", f"{max(queda_restante, 0):.1f}%")
        
        # Projeção restante
        st.subheader("📊 Projeção Restante")
        
        projecao = analisador.projetar_restante_equilibrio(under_inicial_jogo, under_atual, minuto_atual, placar_atual)
        
        if projecao:
            df_projecao = pd.DataFrame(projecao)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Under - Projeção Restante:**")
                st.line_chart(df_projecao.set_index('minuto')['under'])
            
            with col2:
                st.write("**Over - Projeção Restante:**")
                st.line_chart(df_projecao.set_index('minuto')['over'])
            
            # Tabela
            st.subheader(f"📋 Tabela Restante - Min {minuto_atual + 1} ao 90")
            
            df_display = df_projecao[['minuto', 'under', 'over']].copy()
            df_display.columns = ['Minuto', 'Under', 'Over']
            
            st.dataframe(df_display, use_container_width=True, height=300)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("⚽ **Analisador v4.0 - ROBUSTO**")
st.sidebar.markdown("🔒 **100% Monotônico**")
st.sidebar.markdown("✅ **Curva Sempre Decrescente**")
