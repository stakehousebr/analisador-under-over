import streamlit as st
import math
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Analisador Under/Over",
    page_icon="⚽",
    layout="wide"
)

# Classe do analisador CORRIGIDA
class AnalisadorApostasUnderOver:
    def __init__(self):
        self.pontos_equilibrio = {
            1: 42.0, 15: 28.0, 30: 14.0, 35: 12.4, 40: 10.8, 42: 10.0,
            45: 9.1, 46: 8.5, 50: 7.8, 55: 6.2, 60: 4.5, 65: 3.95,
            70: 3.4, 75: 2.9, 80: 2.5, 85: 2.1, 90: 1.50
        }
    
    def calcular_under_final_esperado(self, odd_inicial):
        """CORRIGIDO: Lógica específica para Under baixos"""
        if odd_inicial <= 10.0:  # Under baixo = ajuste especial
            if odd_inicial >= 8.0:
                return 1.15 + (odd_inicial - 8.0) * 0.05  # 1.15 a 1.25
            elif odd_inicial >= 5.0:
                return 1.10 + (odd_inicial - 5.0) * 0.017  # 1.10 a 1.15
            elif odd_inicial >= 3.0:
                return 1.05 + (odd_inicial - 3.0) * 0.025  # 1.05 a 1.10
            else:
                return 1.03 + (odd_inicial - 1.5) * 0.013  # 1.03 a 1.05
        elif odd_inicial >= 40:
            return 1.48 + (odd_inicial - 40) * 0.03
        elif odd_inicial >= 35:
            return 1.45 + (odd_inicial - 35) * 0.02
        elif odd_inicial >= 25:
            return 1.30 + (odd_inicial - 25) * 0.015
        elif odd_inicial >= 19:
            return 1.25 + (odd_inicial - 19) * 0.008
        else:  # 10-19
            return 1.15 + (odd_inicial - 10) * 0.012
    
    def calcular_over_baseado_no_under(self, under_atual):
        """CORRIGIDO: Proteção contra valores inválidos"""
        try:
            # Garante que Under seja no mínimo 1.01
            under_atual = max(under_atual, 1.01)
            
            prob_under = 1 / under_atual
            prob_over = 1 - prob_under
            
            # Proteção contra probabilidade negativa ou zero
            if prob_over <= 0.001:
                return 50.0  # Valor alto mas não 999
            
            over_atual = 1 / prob_over
            
            # Limita Over máximo
            return min(over_atual, 50.0)
            
        except (ZeroDivisionError, ValueError):
            return 50.0
    
    def interpolar_ponto(self, minuto, pontos_ref):
        """Interpolação padrão"""
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
    
    def gerar_curva_equilibrio_90min(self, under_inicial, over_inicial):
        """CORRIGIDO: Lógica especial para Under baixos"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # CORREÇÃO: Lógica especial para Under iniciais baixos
        if under_inicial <= 10.0:
            # Para Under baixos, criar curva personalizada
            pontos_ajustados = self.criar_curva_under_baixo(under_inicial, under_final)
        else:
            # Lógica original para Under altos
            fator_ajuste = under_inicial / 39.0
            pontos_ajustados = {}
            
            for minuto, valor in self.pontos_equilibrio.items():
                if minuto == 90:
                    pontos_ajustados[minuto] = under_final
                else:
                    valor_ajustado = valor * fator_ajuste
                    if valor_ajustado > under_inicial:
                        valor_ajustado = under_inicial * (0.7 + 0.3 * (valor / max(self.pontos_equilibrio.values())))
                    pontos_ajustados[minuto] = max(valor_ajustado, 1.01)  # Limite mínimo
        
        curva = []
        for minuto in range(1, 91):
            under_atual = self.interpolar_ponto(minuto, pontos_ajustados)
            under_atual = max(under_atual, 1.01)  # PROTEÇÃO: Never below 1.01
            over_atual = self.calcular_over_baseado_no_under(under_atual)
            
            curva.append({
                'minuto': minuto,
                'under': round(under_atual, 2),
                'over': round(over_atual, 3)
            })
        
        return curva
    
    def criar_curva_under_baixo(self, under_inicial, under_final):
        """NOVA: Curva especial para Under iniciais baixos"""
        pontos_ajustados = {}
        
        # Pontos chave para Under baixos
        pontos_ajustados[1] = under_inicial
        pontos_ajustados[15] = under_inicial * 0.85  # Queda suave
        pontos_ajustados[30] = under_inicial * 0.65  # Queda moderada
        pontos_ajustados[45] = under_inicial * 0.45  # Queda acelerada
        pontos_ajustados[46] = under_inicial * 0.42  # Início 2º tempo
        pontos_ajustados[60] = under_inicial * 0.35  # Meio 2º tempo
        pontos_ajustados[75] = under_inicial * 0.25  # Reta final
        pontos_ajustados[85] = under_inicial * 0.18  # Últimos minutos
        pontos_ajustados[90] = under_final
        
        # Garante que todos os valores sejam >= 1.01
        for minuto in pontos_ajustados:
            pontos_ajustados[minuto] = max(pontos_ajustados[minuto], 1.01)
        
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
        """Calcula a taxa de queda por minuto"""
        if minutos == 0:
            return 0
        return (under_inicial - under_atual) / (under_inicial * minutos)
    
    def classificar_ritmo(self, taxa_queda):
        """Classifica o ritmo da partida"""
        if taxa_queda >= 0.015:
            return "DESACELERADA ⏰", "Ritmo lento, partida conservadora"
        else:
            return "ACELERADA ⚡", "Ritmo rápido, partida ofensiva"
    
    def analisar_melhor_entrada_under(self, curva):
        """Encontra os melhores momentos para entrada Under"""
        melhores_entradas = []
        
        for i in range(14, 65, 5):
            if i + 10 < len(curva):
                odd_entrada = curva[i]['under']
                odd_10min_depois = curva[i + 10]['under']
                
                # Proteção contra valores inválidos
                if odd_entrada > 1.01 and odd_10min_depois > 1.01:
                    queda_percent = ((odd_entrada - odd_10min_depois) / odd_entrada) * 100
                    
                    if 1.1 <= odd_entrada <= 35.0 and queda_percent >= 8:
                        melhores_entradas.append({
                            'minuto': i + 1,
                            'odd_entrada': odd_entrada,
                            'odd_apos_10min': odd_10min_depois,
                            'queda_percent': round(queda_percent, 1),
                            'potencial_lucro': f"{queda_percent:.1f}%"
                        })
        
        return sorted(melhores_entradas, key=lambda x: x['queda_percent'], reverse=True)[:3]
    
    def analisar_melhor_entrada_over(self, curva):
        """Encontra os melhores momentos para entrada Over"""
        melhores_entradas = []
        
        for i in range(59, 85, 3):
            if i < len(curva):
                odd_over = curva[i]['over']
                under_atual = curva[i]['under']
                under_final = curva[89]['under']
                
                over_final = self.calcular_over_baseado_no_under(under_final)
                
                if over_final > odd_over and odd_over < 25.0:  # Evita Over muito alto
                    risco_correcao = ((over_final - odd_over) / odd_over) * 100
                else:
                    risco_correcao = 0
                
                if odd_over >= 1.1 and risco_correcao <= 60 and odd_over <= 25.0:
                    melhores_entradas.append({
                        'minuto': i + 1,
                        'odd_entrada': odd_over,
                        'under_atual': under_atual,
                        'risco_correcao': round(risco_correcao, 1),
                        'estabilidade': 'Alta' if risco_correcao < 20 else 'Média'
                    })
        
        return sorted(melhores_entradas, key=lambda x: x['risco_correcao'])[:3]
    
    def projetar_restante_equilibrio(self, under_inicial, under_atual, minuto_atual, placar):
        """Projeta o restante usando curva de equilíbrio"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        pontos_restantes = {}
        pontos_restantes[minuto_atual] = max(under_atual, 1.01)  # Proteção
        
        # Lógica especial para Under baixos
        if under_inicial <= 10.0:
            pontos_ajustados = self.criar_curva_under_baixo(under_inicial, under_final)
            fator_ajuste_atual = under_atual / self.interpolar_ponto(minuto_atual, pontos_ajustados)
        else:
            fator_ajuste_atual = under_atual / self.interpolar_ponto(minuto_atual, self.pontos_equilibrio)
        
        for minuto in range(minuto_atual + 1, 91):
            if minuto == 90:
                pontos_restantes[minuto] = under_final
            else:
                if under_inicial <= 10.0:
                    valor_ref = self.interpolar_ponto(minuto, self.criar_curva_under_baixo(under_inicial, under_final))
                else:
                    valor_ref = self.interpolar_ponto(minuto, self.pontos_equilibrio)
                
                if minuto <= minuto_atual + 15:
                    pontos_restantes[minuto] = max(valor_ref * fator_ajuste_atual, 1.01)
                else:
                    peso_ajuste = (90 - minuto) / (90 - minuto_atual - 15)
                    valor_ajustado = valor_ref * (1 + (fator_ajuste_atual - 1) * peso_ajuste * 0.5)
                    pontos_restantes[minuto] = max(valor_ajustado, 1.01)
        
        projecao = []
        
        for i in range(minuto_atual + 1, 91):
            under_projetado = max(self.interpolar_ponto(i, pontos_restantes), 1.01)
            over_projetado = self.calcular_over_baseado_no_under(under_projetado)
            
            projecao.append({
                'minuto': i,
                'under': round(under_projetado, 2),
                'over': round(over_projetado, 3)
            })
        
        return projecao

# Interface Streamlit
st.title("🎯 Analisador Profissional Under/Over v3.1")
st.subheader("🔄 Curva de Equilíbrio Real - CORRIGIDA")

# Sidebar
st.sidebar.header("⚙️ Configurações")

modo = st.sidebar.selectbox(
    "📊 Selecione o Modo:",
    ["🎯 Jogo em Andamento", "📈 Projeção Completa"]
)

if modo == "📈 Projeção Completa":
    st.sidebar.subheader("📋 Dados Iniciais")
    under_inicial = st.sidebar.number_input("Under Inicial:", value=7.20, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial = st.sidebar.number_input("Over Inicial:", value=1.15, min_value=1.01, max_value=999.0, step=0.01)
    
    if st.sidebar.button("🚀 Executar Análise", type="primary"):
        analisador = AnalisadorApostasUnderOver()
        
        st.header("📊 Projeção Completa (90 Minutos)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Under Inicial", f"{under_inicial}")
            st.metric("Over Inicial", f"{over_inicial}")
        
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial, over_inicial)
        
        with col2:
            st.metric("Under Final", f"{curva[89]['under']}")
            st.metric("Over Final", f"{curva[89]['over']}")
        
        # Alertas para Under baixos
        if under_inicial <= 10.0:
            st.warning("⚠️ **Under Baixo Detectado** - Usando curva especializada para Under iniciais baixos")
        
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
        
        # Criar tabela formatada
        df_display = df_curva.copy()
        df_display['Minuto'] = df_display['minuto']
        df_display['Under'] = df_display['under']
        df_display['Over'] = df_display['over'].round(3)
        df_display = df_display[['Minuto', 'Under', 'Over']]
        
        st.dataframe(df_display, use_container_width=True, height=400)

else:
    st.sidebar.subheader("📋 Dados do Jogo")
    placar_atual = st.sidebar.text_input("Placar Atual:", value="2x0")
    under_inicial_jogo = st.sidebar.number_input("Under Inicial:", value=7.20, min_value=1.01, max_value=999.0, step=0.1)
    over_inicial_jogo = st.sidebar.number_input("Over Inicial:", value=1.15, min_value=1.01, max_value=999.0, step=0.01)
    under_atual = st.sidebar.number_input("Under Atual:", value=5.0, min_value=1.01, max_value=999.0, step=0.1)
    over_atual = st.sidebar.number_input("Over Atual:", value=1.25, min_value=1.01, max_value=999.0, step=0.01)
    minuto_atual = st.sidebar.slider("Minuto Atual:", min_value=1, max_value=89, value=15)
    
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
        
        # Alerta para Under baixos
        if under_inicial_jogo <= 10.0:
            st.info("ℹ️ **Under Baixo** - Usando algoritmo especializado")
        
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
            df_display['Minuto'] = df_display['minuto']
            df_display['Under'] = df_display['under']
            df_display['Over'] = df_display['over'].round(3)
            df_display = df_display[['Minuto', 'Under', 'Over']]
            
            st.dataframe(df_display, use_container_width=True, height=400)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("⚽ **Analisador Under/Over v3.1**")
st.sidebar.markdown("🔧 **CORRIGIDO** - Under Baixos")
st.sidebar.markdown("🔄 Curva de Equilíbrio Real")
