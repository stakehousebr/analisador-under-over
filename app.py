import streamlit as st
import math
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Analisador Under/Over",
    page_icon="⚽",
    layout="wide"
)

# Classe do analisador FINAL CORRIGIDA
class AnalisadorApostasUnderOver:
    def __init__(self):
        self.pontos_equilibrio = {
            1: 42.0, 15: 28.0, 30: 14.0, 35: 12.4, 40: 10.8, 42: 10.0,
            45: 9.1, 46: 8.5, 50: 7.8, 55: 6.2, 60: 4.5, 65: 3.95,
            70: 3.4, 75: 2.9, 80: 2.5, 85: 2.1, 90: 1.50
        }
    
    def calcular_under_final_esperado(self, odd_inicial):
        """CORRIGIDO: Lógica mais precisa por faixas"""
        if odd_inicial >= 40:
            return 1.48 + (odd_inicial - 40) * 0.03
        elif odd_inicial >= 30:
            return 1.40 + (odd_inicial - 30) * 0.008
        elif odd_inicial >= 20:
            return 1.30 + (odd_inicial - 20) * 0.010
        elif odd_inicial >= 15:
            return 1.25 + (odd_inicial - 15) * 0.010
        elif odd_inicial >= 10:
            return 1.20 + (odd_inicial - 10) * 0.010
        elif odd_inicial >= 7:
            return 1.15 + (odd_inicial - 7) * 0.017
        elif odd_inicial >= 5:
            return 1.10 + (odd_inicial - 5) * 0.025
        elif odd_inicial >= 3:
            return 1.05 + (odd_inicial - 3) * 0.025
        else:
            return 1.03
    
    def calcular_over_baseado_no_under(self, under_atual):
        """CORRIGIDO: Cálculo mais natural"""
        try:
            under_atual = max(under_atual, 1.01)
            prob_under = 1 / under_atual
            prob_over = 1 - prob_under
            
            if prob_over <= 0.001:
                return 25.0
            
            over_atual = 1 / prob_over
            return min(over_atual, 25.0)  # Limite mais baixo
            
        except (ZeroDivisionError, ValueError):
            return 25.0
    
    def interpolar_ponto(self, minuto, pontos_ref):
        """Interpolação suave"""
        if minuto in pontos_ref:
            return pontos_ref[minuto]
        
        minutos_sorted = sorted(pontos_ref.keys())
        if minuto < minutos_sorted[0]:
            return pontos_ref[minutos_sorted[0]]
        if minuto > minutos_sorted[-1]:
            return pontos_ref[minutos_sorted[-1]]
        
        for i in range(len(minutos_sorted) - 1):
            min1, min2 = minutos_sorted[i], minutos_sorted[i + 1]
            if min1 <= minuto <= min2:
                val1, val2 = pontos_ref[min1], pontos_ref[min2]
                fator = (minuto - min1) / (min2 - min1)
                return val1 + (val2 - val1) * fator
        
        return pontos_ref[minutos_sorted[-1]]
    
    def classificar_under_inicial(self, under_inicial):
        """Classifica o tipo de Under inicial"""
        if under_inicial >= 30:
            return "ALTO"
        elif under_inicial >= 15:
            return "MEDIO"
        elif under_inicial >= 7:
            return "MEDIO_BAIXO" 
        else:
            return "BAIXO"
    
    def gerar_curva_equilibrio_90min(self, under_inicial, over_inicial):
        """CORRIGIDO: Lógica por classificação de Under"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        tipo_under = self.classificar_under_inicial(under_inicial)
        
        if tipo_under == "ALTO":
            # Under alto (30+): Usar lógica original
            fator_ajuste = under_inicial / 39.0
            pontos_ajustados = {}
            
            for minuto, valor in self.pontos_equilibrio.items():
                if minuto == 90:
                    pontos_ajustados[minuto] = under_final
                else:
                    valor_ajustado = valor * fator_ajuste
                    pontos_ajustados[minuto] = valor_ajustado
                    
        elif tipo_under == "MEDIO":
            # Under médio (15-30): Lógica ajustada
            pontos_ajustados = self.criar_curva_under_medio(under_inicial, under_final)
            
        elif tipo_under == "MEDIO_BAIXO":
            # Under médio-baixo (7-15): Lógica especial
            pontos_ajustados = self.criar_curva_under_medio_baixo(under_inicial, under_final)
            
        else:
            # Under baixo (<7): Lógica conservadora
            pontos_ajustados = self.criar_curva_under_baixo(under_inicial, under_final)
        
        # Gerar curva final
        curva = []
        for minuto in range(1, 91):
            under_atual = self.interpolar_ponto(minuto, pontos_ajustados)
            under_atual = max(under_atual, 1.01)
            over_atual = self.calcular_over_baseado_no_under(under_atual)
            
            curva.append({
                'minuto': minuto,
                'under': round(under_atual, 2),
                'over': round(over_atual, 3)
            })
        
        return curva
    
    def criar_curva_under_medio(self, under_inicial, under_final):
        """NOVA: Curva para Under médios (15-30)"""
        pontos_ajustados = {}
        
        # Proporção baseada na referência Under 20 → 1.30
        referencia_inicial = 20.0
        referencia_final = 1.30
        
        fator_inicial = under_inicial / referencia_inicial
        fator_final = under_final / referencia_final
        
        pontos_ajustados[1] = under_inicial
        pontos_ajustados[15] = under_inicial * 0.70   # Queda moderada
        pontos_ajustados[30] = under_inicial * 0.50   # Meio primeiro tempo
        pontos_ajustados[35] = under_inicial * 0.45   # Final primeiro tempo
        pontos_ajustados[45] = under_inicial * 0.35   # Intervalo
        pontos_ajustados[46] = under_inicial * 0.32   # Início segundo tempo
        pontos_ajustados[60] = under_inicial * 0.25   # Meio segundo tempo
        pontos_ajustados[75] = under_inicial * 0.18   # Reta final
        pontos_ajustados[85] = under_inicial * 0.12   # Últimos minutos
        pontos_ajustados[90] = under_final
        
        return pontos_ajustados
    
    def criar_curva_under_medio_baixo(self, under_inicial, under_final):
        """NOVA: Curva para Under médio-baixos (7-15)"""
        pontos_ajustados = {}
        
        pontos_ajustados[1] = under_inicial
        pontos_ajustados[15] = under_inicial * 0.75   # Queda mais suave
        pontos_ajustados[30] = under_inicial * 0.60   
        pontos_ajustados[35] = under_inicial * 0.55   
        pontos_ajustados[45] = under_inicial * 0.45   
        pontos_ajustados[46] = under_inicial * 0.42   
        pontos_ajustados[60] = under_inicial * 0.35   
        pontos_ajustados[75] = under_inicial * 0.25   
        pontos_ajustados[85] = under_inicial * 0.15   
        pontos_ajustados[90] = under_final
        
        return pontos_ajustados
    
    def criar_curva_under_baixo(self, under_inicial, under_final):
        """CORRIGIDA: Curva para Under baixos (<7)"""
        pontos_ajustados = {}
        
        pontos_ajustados[1] = under_inicial
        pontos_ajustados[15] = under_inicial * 0.85   # Queda muito suave
        pontos_ajustados[30] = under_inicial * 0.70   
        pontos_ajustados[35] = under_inicial * 0.65   
        pontos_ajustados[45] = under_inicial * 0.55   
        pontos_ajustados[46] = under_inicial * 0.52   
        pontos_ajustados[60] = under_inicial * 0.45   
        pontos_ajustados[75] = under_inicial * 0.35   
        pontos_ajustados[85] = under_inicial * 0.25   
        pontos_ajustados[90] = under_final
        
        return pontos_ajustados
    
    def analisar_divergencia(self, under_atual_real, under_esperado, minuto):
        """Análise de divergência"""
        divergencia_percent = ((under_atual_real - under_esperado) / under_esperado) * 100
        
        if divergencia_percent >= 15:
            status = "🔥 OPORTUNIDADE ALTA"
            explicacao = "Odd atual muito ACIMA da projetada - Correção forte esperada!"
            recomendacao = "✅ EXCELENTE momento para entrada Under"
            risco = "Baixo"
        elif divergencia_percent >= 8:
            status = "💰 OPORTUNIDADE MÉDIA"
            explicacao = "Odd atual ACIMA da projetada - Correção moderada esperada"
            recomendacao = "✅ Bom momento para entrada Under"
            risco = "Médio"
        elif divergencia_percent >= -8:
            status = "⚖️ EQUILIBRADO"
            explicacao = "Odd atual próxima da projetada - Mercado alinhado"
            recomendacao = "⚠️ Entrada neutra - Risco/benefício equilibrado"
            risco = "Médio"
        elif divergencia_percent >= -15:
            status = "⚠️ CUIDADO"
            explicacao = "Odd atual ABAIXO da projetada - Pouco potencial de queda"
            recomendacao = "❌ Entrada Under arriscada - Pouco retorno esperado"
            risco = "Alto"
        else:
            status = "🚨 RISCO ALTO"
            explicacao = "Odd atual muito ABAIXO da projetada - Mercado pode estar travado"
            recomendacao = "❌ EVITAR entrada Under - Exposição desnecessária"
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
        
        for i in range(14, 65, 5):
            if i + 10 < len(curva):
                odd_entrada = curva[i]['under']
                odd_10min_depois = curva[i + 10]['under']
                
                if odd_entrada > 1.10 and odd_10min_depois > 1.05:
                    queda_percent = ((odd_entrada - odd_10min_depois) / odd_entrada) * 100
                    
                    if queda_percent >= 8:
                        melhores_entradas.append({
                            'minuto': i + 1,
                            'odd_entrada': odd_entrada,
                            'odd_apos_10min': odd_10min_depois,
                            'queda_percent': round(queda_percent, 1),
                            'potencial_lucro': f"{queda_percent:.1f}%"
                        })
        
        return sorted(melhores_entradas, key=lambda x: x['queda_percent'], reverse=True)[:3]
    
    def analisar_melhor_entrada_over(self, curva):
        melhores_entradas = []
        
        for i in range(59, 85, 3):
            if i < len(curva):
                odd_over = curva[i]['over']
                under_atual = curva[i]['under']
                under_final = curva[89]['under']
                
                over_final = self.calcular_over_baseado_no_under(under_final)
                
                if over_final > odd_over and odd_over < 15.0:
                    risco_correcao = ((over_final - odd_over) / odd_over) * 100
                else:
                    risco_correcao = 0
                
                if odd_over >= 1.15 and risco_correcao <= 60:
                    melhores_entradas.append({
                        'minuto': i + 1,
                        'odd_entrada': odd_over,
                        'under_atual': under_atual,
                        'risco_correcao': round(risco_correcao, 1),
                        'estabilidade': 'Alta' if risco_correcao < 20 else 'Média'
                    })
        
        return sorted(melhores_entradas, key=lambda x: x['risco_correcao'])[:3]
    
    def projetar_restante_equilibrio(self, under_inicial, under_atual, minuto_atual, placar):
        under_final = self.calcular_under_final_esperado(under_inicial)
        tipo_under = self.classificar_under_inicial(under_inicial)
        
        # Criar pontos de referência baseado no tipo
        if tipo_under == "ALTO":
            pontos_referencia = self.pontos_equilibrio
        elif tipo_under == "MEDIO":
            pontos_referencia = self.criar_curva_under_medio(under_inicial, under_final)
        elif tipo_under == "MEDIO_BAIXO":
            pontos_referencia = self.criar_curva_under_medio_baixo(under_inicial, under_final)
        else:
            pontos_referencia = self.criar_curva_under_baixo(under_inicial, under_final)
        
        pontos_restantes = {}
        pontos_restantes[minuto_atual] = under_atual
        
        # Ajustar pontos restantes
        for minuto in range(minuto_atual + 1, 91):
            if minuto == 90:
                pontos_restantes[minuto] = under_final
            else:
                valor_ref = self.interpolar_ponto(minuto, pontos_referencia)
                # Suavizar transição
                peso = (minuto - minuto_atual) / (90 - minuto_atual)
                valor_ajustado = under_atual * (1 - peso) + valor_ref * peso
                pontos_restantes[minuto] = max(valor_ajustado, 1.01)
        
        projecao = []
        for i in range(minuto_atual + 1, 91):
            under_projetado = self.interpolar_ponto(i, pontos_restantes)
            under_projetado = max(under_projetado, 1.01)
            over_projetado = self.calcular_over_baseado_no_under(under_projetado)
            
            projecao.append({
                'minuto': i,
                'under': round(under_projetado, 2),
                'over': round(over_projetado, 3)
            })
        
        return projecao

# Interface Streamlit
st.title("🎯 Analisador Profissional Under/Over v3.2")
st.subheader("🔄 Curva de Equilíbrio Real - FINAL")

# Sidebar
st.sidebar.header("⚙️ Configurações")

modo = st.sidebar.selectbox(
    "📊 Selecione o Modo:",
    ["🎯 Jogo em Andamento", "📈 Projeção Completa"]
)

if modo == "📈 Projeção Completa":
    st.sidebar.subheader("📋 Dados Iniciais")
    under_inicial = st.sidebar.number_input("Under Inicial:", value=13.0, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial = st.sidebar.number_input("Over Inicial:", value=1.06, min_value=1.01, max_value=999.0, step=0.01)
    
    if st.sidebar.button("🚀 Executar Análise", type="primary"):
        analisador = AnalisadorApostasUnderOver()
        
        # Classificação do Under
        tipo_under = analisador.classificar_under_inicial(under_inicial)
        
        st.header("📊 Projeção Completa (90 Minutos)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Under Inicial", f"{under_inicial}")
            st.metric("Over Inicial", f"{over_inicial}")
            st.info(f"📊 **Classificação:** Under {tipo_under}")
        
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial, over_inicial)
        
        with col2:
            st.metric("Under Final", f"{curva[89]['under']}")
            st.metric("Over Final", f"{curva[89]['over']}")
            
            # Potencial de queda
            queda_total = ((under_inicial - curva[89]['under']) / under_inicial) * 100
            st.metric("Potencial Total", f"{queda_total:.1f}%")
        
        # Gráficos
        df_curva = pd.DataFrame(curva)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolução Under")
            st.line_chart(df_curva.set_index('minuto')['under'])
        
        with col2:
            st.subheader("📈 Evolução Over")
            st.line_chart(df_curva.set_index('minuto')['over'])
        
        # Estratégias de entrada
        st.subheader("🎯 Estratégias de Entrada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("💎 **Top 3 Entradas Under:**")
            melhores_under = analisador.analisar_melhor_entrada_under(curva)
            if melhores_under:
                for i, entrada in enumerate(melhores_under, 1):
                    st.write(f"{i}. Min {entrada['minuto']}: {entrada['odd_entrada']} → {entrada['odd_apos_10min']} ({entrada['potencial_lucro']})")
            else:
                st.write("❌ Nenhuma entrada Under favorável")
        
        with col2:
            st.write("🚀 **Top 3 Entradas Over:**")
            melhores_over = analisador.analisar_melhor_entrada_over(curva)
            if melhores_over:
                for i, entrada in enumerate(melhores_over, 1):
                    st.write(f"{i}. Min {entrada['minuto']}: {entrada['odd_entrada']:.3f} (Risco: {entrada['risco_correcao']}%)")
            else:
                st.write("❌ Nenhuma entrada Over favorável")
        
        # Tabela completa minuto a minuto
        st.subheader("📊 Tabela Completa Minuto a Minuto")
        
        df_display = df_curva.copy()
        df_display['Minuto'] = df_display['minuto']
        df_display['Under'] = df_display['under']
        df_display['Over'] = df_display['over'].round(3)
        df_display = df_display[['Minuto', 'Under', 'Over']]
        
        st.dataframe(df_display, use_container_width=True, height=400)

else:
    st.sidebar.subheader("📋 Dados do Jogo")
    placar_atual = st.sidebar.text_input("Placar Atual:", value="1x1")
    under_inicial_jogo = st.sidebar.number_input("Under Inicial:", value=13.0, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial_jogo = st.sidebar.number_input("Over Inicial:", value=1.06, min_value=1.01, max_value=999.0, step=0.01)
    under_atual = st.sidebar.number_input("Under Atual:", value=9.0, min_value=1.01, max_value=999.0, step=0.1)
    over_atual = st.sidebar.number_input("Over Atual:", value=1.12, min_value=1.01, max_value=999.0, step=0.01)
    minuto_atual = st.sidebar.slider("Minuto Atual:", min_value=1, max_value=89, value=15)
    
    if st.sidebar.button("🚀 Executar Análise", type="primary"):
        analisador = AnalisadorApostasUnderOver()
        
        tipo_under = analisador.classificar_under_inicial(under_inicial_jogo)
        
        st.header("📊 Jogo em Andamento")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Placar", placar_atual)
            st.metric("Minuto", f"{minuto_atual}'")
        
        with col2:
            st.metric("Under", f"{under_inicial_jogo} → {under_atual}")
            
        with col3:
            st.metric("Over", f"{over_inicial_jogo} → {over_atual}")
        
        st.info(f"📊 **Under Classificado:** {tipo_under}")
        
        # Análise
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial_jogo, over_inicial_jogo)
        under_esperado = curva[minuto_atual - 1]['under']
        over_esperado = curva[minuto_atual - 1]['over']
        
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
        
        # Análise de ritmo
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
        queda_restante = ((under_atual - under_final) / under_atual) * 100
        
        st.subheader("🎯 Projeção Final")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Under Final", f"{under_final:.2f}")
        
        with col2:
            st.metric("Over Final", f"{over_final:.3f}")
        
        with col3:
            if queda_restante > 25:
                potencial = "🔥 MUITO ALTO"
            elif queda_restante > 15:
                potencial = "💰 ALTO"
            elif queda_restante > 8:
                potencial = "⚖️ MÉDIO"
            else:
                potencial = "⚠️ BAIXO"
            
            st.metric("Potencial Under", potencial)
            st.metric("Queda Restante", f"{queda_restante:.1f}%")
        
        # Projeção restante
        st.subheader("📊 Projeção Restante")
        
        projecao = analisador.projetar_restante_equilibrio(under_inicial_jogo, under_atual, minuto_atual, placar_atual)
        
        if projecao:
            df_projecao = pd.DataFrame(projecao)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Gráfico da Projeção Restante:**")
                st.line_chart(df_projecao.set_index('minuto')[['under']])
            
            with col2:
                st.write("**Evolução Over:**")
                st.line_chart(df_projecao.set_index('minuto')[['over']])
            
            # Tabela restante minuto a minuto
            st.subheader(f"📋 Tabela Restante - Minuto {minuto_atual + 1} ao 90")
            
            df_display = df_projecao.copy()
            df_display['Minuto'] = df_projecao['minuto']
            df_display['Under'] = df_projecao['under']
            df_display['Over'] = df_projecao['over'].round(3)
            df_display = df_display[['Minuto', 'Under', 'Over']]
            
            st.dataframe(df_display, use_container_width=True, height=400)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("⚽ **Analisador Under/Over v3.2**")
st.sidebar.markdown("🎯 **FINAL** - Todas Faixas")
st.sidebar.markdown("🔄 Curva de Equilíbrio Real")
