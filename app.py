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
        pass
    
    def calcular_under_final_esperado(self, under_inicial):
        """Cálculo mais equilibrado do Under final"""
        if under_inicial >= 50:
            return max(1.50, under_inicial * 0.035)
        elif under_inicial >= 30:
            return max(1.40, under_inicial * 0.045) 
        elif under_inicial >= 20:
            return max(1.30, under_inicial * 0.055)
        elif under_inicial >= 15:
            return max(1.25, under_inicial * 0.070)
        elif under_inicial >= 10:
            return max(1.20, under_inicial * 0.110)
        elif under_inicial >= 7:
            return max(1.15, under_inicial * 0.150)  # 7 × 0.15 = 1.05, limitado a 1.15
        elif under_inicial >= 5:
            return max(1.10, under_inicial * 0.200)
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
    
    def criar_curva_natural(self, under_inicial, under_final):
        """NOVA: Cria curva natural baseada em função matemática"""
        
        # Calcula a diferença total que precisa ser distribuída
        diferenca_total = under_inicial - under_final
        
        # Define velocidades de queda por período
        velocidades = {
            'periodo_1_15': 0.25,    # 25% da queda total nos primeiros 15 min
            'periodo_15_30': 0.20,   # 20% da queda nos próximos 15 min
            'periodo_30_45': 0.20,   # 20% da queda nos próximos 15 min
            'periodo_45_60': 0.15,   # 15% da queda nos próximos 15 min
            'periodo_60_75': 0.12,   # 12% da queda nos próximos 15 min
            'periodo_75_90': 0.08    # 8% da queda nos últimos 15 min
        }
        
        # Calcula pontos de controle
        pontos = {}
        valor_atual = under_inicial
        
        # Minuto 1
        pontos[1] = under_inicial
        
        # Minuto 15
        queda_15 = diferenca_total * velocidades['periodo_1_15']
        valor_atual -= queda_15
        pontos[15] = max(valor_atual, under_final)
        
        # Minuto 30
        queda_30 = diferenca_total * velocidades['periodo_15_30']
        valor_atual -= queda_30
        pontos[30] = max(valor_atual, under_final)
        
        # Minuto 45
        queda_45 = diferenca_total * velocidades['periodo_30_45']
        valor_atual -= queda_45
        pontos[45] = max(valor_atual, under_final)
        
        # Minuto 46 (pequeno boost no início do 2º tempo)
        boost_2tempo = (pontos[45] - under_final) * 0.95  # Pequena aceleração
        pontos[46] = max(pontos[45] - (pontos[45] - under_final) * 0.05, under_final)
        
        # Minuto 60
        queda_60 = diferenca_total * velocidades['periodo_45_60']
        valor_atual -= queda_60
        pontos[60] = max(valor_atual, under_final)
        
        # Minuto 75
        queda_75 = diferenca_total * velocidades['periodo_60_75']
        valor_atual -= queda_75
        pontos[75] = max(valor_atual, under_final)
        
        # Minuto 85 (penúltimo ponto)
        queda_85 = diferenca_total * velocidades['periodo_75_90'] * 0.7  # 70% da queda final
        valor_atual -= queda_85
        pontos[85] = max(valor_atual, under_final)
        
        # Minuto 90 (final)
        pontos[90] = under_final
        
        # VERIFICAÇÃO: Garante progressão decrescente
        minutos_ordenados = sorted(pontos.keys())
        for i in range(1, len(minutos_ordenados)):
            min_atual = minutos_ordenados[i]
            min_anterior = minutos_ordenados[i-1]
            
            if pontos[min_atual] >= pontos[min_anterior]:
                # Corrige forçando uma pequena queda
                pontos[min_atual] = pontos[min_anterior] * 0.98
                pontos[min_atual] = max(pontos[min_atual], under_final)
        
        return pontos
    
    def interpolar_suave(self, minuto, pontos_curva):
        """Interpolação suave que mantém progressão natural"""
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
                
                # Interpolação com curva suave (não linear)
                fator = (minuto - min1) / (min2 - min1)
                
                # Aplica suavização exponencial para evitar quedas muito lineares
                fator_suave = 1 - math.exp(-2 * fator)  # Curva exponencial suave
                
                valor = val1 + (val2 - val1) * fator_suave
                
                # Garante que não suba
                return min(valor, val1)
        
        return pontos_curva[minutos_ordenados[-1]]
    
    def gerar_curva_equilibrio_90min(self, under_inicial, over_inicial):
        """Gera curva natural e equilibrada"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Cria pontos de controle naturais
        pontos_curva = self.criar_curva_natural(under_inicial, under_final)
        
        # Debug: Mostra pontos de controle
        if st.sidebar.checkbox("🔍 Mostrar Pontos de Controle", False):
            st.sidebar.write("**Pontos de Controle:**")
            for min_key, valor in sorted(pontos_curva.items()):
                st.sidebar.write(f"Min {min_key}: {valor:.2f}")
        
        # Gera curva completa minuto a minuto
        curva = []
        valor_anterior = under_inicial
        
        for minuto in range(1, 91):
            under_atual = self.interpolar_suave(minuto, pontos_curva)
            
            # Dupla verificação: garante progressão decrescente
            under_atual = min(under_atual, valor_anterior)
            under_atual = max(under_atual, under_final)  # Nunca abaixo do final
            under_atual = max(under_atual, 1.01)         # Mínimo absoluto
            
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
    
    def analisar_distribuicao_queda(self, curva):
        """NOVA: Analisa como a queda está distribuída"""
        under_inicial = curva[0]['under']
        
        # Análise por períodos
        periodos = {
            '1º Tempo (1-45)': (curva[0]['under'], curva[44]['under']),
            '2º Tempo (46-90)': (curva[45]['under'], curva[89]['under']),
            'Primeiro Terço (1-30)': (curva[0]['under'], curva[29]['under']),
            'Segundo Terço (31-60)': (curva[30]['under'], curva[59]['under']),
            'Terceiro Terço (61-90)': (curva[60]['under'], curva[89]['under'])
        }
        
        análise = {}
        for periodo, (valor_inicio, valor_fim) in periodos.items():
            queda = valor_inicio - valor_fim
            percentual = (queda / under_inicial) * 100
            análise[periodo] = {
                'queda_absoluta': round(queda, 2),
                'queda_percentual': round(percentual, 1)
            }
        
        return análise
    
    def analisar_melhor_entrada_under(self, curva):
        melhores_entradas = []
        
        for i in range(10, 70, 5):  # Analisa a cada 5 minutos até o minuto 70
            if i + 15 < len(curva):  # Janela de 15 minutos
                odd_entrada = curva[i]['under']
                odd_depois = curva[i + 15]['under']
                
                if odd_entrada > 1.30 and odd_depois > 1.10:
                    queda_percent = ((odd_entrada - odd_depois) / odd_entrada) * 100
                    
                    if queda_percent >= 8:  # Mínimo 8% de queda
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
        
        for i in range(65, 85, 3):  # Foco nos últimos 25 minutos
            if i < len(curva):
                odd_over = curva[i]['over']
                
                if 1.8 <= odd_over <= 12.0:  # Range mais equilibrado
                    melhores_entradas.append({
                        'minuto': i + 1,
                        'odd_entrada': odd_over,
                        'estabilidade': 'Alta' if odd_over <= 6.0 else 'Média'
                    })
        
        return melhores_entradas[:3]
    
    def projetar_restante_equilibrio(self, under_inicial, under_atual, minuto_atual, placar):
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Calcula quantos minutos restam
        minutos_restantes = 90 - minuto_atual
        diferenca_restante = under_atual - under_final
        
        # Taxa de queda constante para o restante
        if minutos_restantes > 0:
            taxa_queda_restante = diferenca_restante / minutos_restantes
        else:
            taxa_queda_restante = 0
        
        # Cria projeção minuto a minuto
        projecao = []
        valor_atual = under_atual
        
        for minuto in range(minuto_atual + 1, 91):
            # Aplicar queda gradual
            valor_atual -= taxa_queda_restante
            valor_atual = max(valor_atual, under_final)  # Nunca abaixo do final
            
            over_proj = self.calcular_over_baseado_no_under(valor_atual)
            
            projecao.append({
                'minuto': minuto,
                'under': round(valor_atual, 2),
                'over': round(over_proj, 3)
            })
        
        return projecao

# Interface Streamlit
st.title("🎯 Analisador Under/Over v5.0 - NATURAL")
st.subheader("📊 Curva Equilibrada e Realista")

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
            st.success("✅ **Curva Natural:** Queda equilibrada")
        
        curva = analisador.gerar_curva_equilibrio_90min(under_inicial, over_inicial)
        
        with col2:
            st.metric("Under Final", f"{curva[89]['under']}")
            st.metric("Over Final", f"{curva[89]['over']}")
            
            # Queda total
            queda_total = under_inicial - curva[89]['under']
            percentual_total = (queda_total / under_inicial) * 100
            st.metric("Queda Total", f"{percentual_total:.1f}%")
        
        # Análise de distribuição da queda
        st.subheader("📊 Distribuição da Queda por Períodos")
        
        distribuicao = analisador.analisar_distribuicao_queda(curva)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**⏰ Por Tempo:**")
            for periodo in ['1º Tempo (1-45)', '2º Tempo (46-90)']:
                dados = distribuicao[periodo]
                st.write(f"• {periodo.split(' ')[0]} {periodo.split(' ')[1]}: {dados['queda_percentual']}%")
        
        with col2:
            st.write("**📈 Por Terços:**")
            for periodo in ['Primeiro Terço (1-30)', 'Segundo Terço (31-60)', 'Terceiro Terço (61-90)']:
                dados = distribuicao[periodo]
                terco = periodo.split(' ')[0]
                st.write(f"• {terco}: {dados['queda_percentual']}%")
        
        with col3:
            # Verificação de equilíbrio
            primeiro_tempo = distribuicao['1º Tempo (1-45)']['queda_percentual']
            segundo_tempo = distribuicao['2º Tempo (46-90)']['queda_percentual']
            
            if segundo_tempo < 5:
                st.warning("⚠️ 2º tempo muito lento")
            elif abs(primeiro_tempo - segundo_tempo) < 15:
                st.success("✅ Distribuição equilibrada")
            else:
                st.info("ℹ️ Distribuição assimétrica")
        
        # Gráficos
        df_curva = pd.DataFrame(curva)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Evolução Under (Natural)")
            st.line_chart(df_curva.set_index('minuto')['under'])
        
        with col2:
            st.subheader("📈 Evolução Over")
            st.line_chart(df_curva.set_index('minuto')['over'])
        
        # Verificação de consistência
        st.subheader("🔍 Verificação de Consistência")
        
        problemas = []
        for i in range(1, len(curva)):
            if curva[i]['under'] > curva[i-1]['under']:
                problemas.append(f"Min {curva[i]['minuto']}: {curva[i]['under']} > {curva[i-1]['under']}")
        
        if problemas:
            st.error(f"❌ **{len(problemas)} problemas encontrados**")
            for problema in problemas[:3]:
                st.write(f"• {problema}")
        else:
            st.success("✅ **Perfeito!** Curva sempre decrescente")
        
        # Análise de períodos críticos
        under_60 = curva[59]['under']  # Minuto 60
        under_90 = curva[89]['under']  # Minuto 90
        queda_segundo_tempo = under_60 - under_90
        percentual_segundo_tempo = (queda_segundo_tempo / under_60) * 100
        
        if percentual_segundo_tempo < 10:
            st.warning("⚠️ **Atenção:** Segundo tempo com pouca movimentação")
        else:
            st.success(f"✅ **Segundo tempo ativo:** {percentual_segundo_tempo:.1f}% de queda")
        
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
                st.write("❌ Nenhuma oportunidade Under clara")
        
        with col2:
            st.write("🚀 **Entradas Over Equilibradas:**")
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
    under_atual = st.sidebar.number_input("Under Atual:", value=4.5, min_value=1.01, max_value=999.0, step=0.1)
    over_atual = st.sidebar.number_input("Over Atual:", value=1.28, min_value=1.01, max_value=999.0, step=0.01)
    minuto_atual = st.sidebar.slider("Minuto Atual:", min_value=1, max_value=89, value=25)
    
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
            if queda_restante > 35:
                potencial = "🔥 MUITO ALTO"
            elif queda_restante > 25:
                potencial = "💰 ALTO"
            elif queda_restante > 15:
                potencial = "⚖️ MÉDIO"
            else:
                potencial = "⚠️ BAIXO"
            
            st.metric("Potencial Under", potencial)
            st.metric("Queda Restante", f"{max(queda_restante, 0):.1f}%")
        
        # Projeção restante
        st.subheader("📊 Projeção Restante (Queda Gradual)")
        
        projecao = analisador.projetar_restante_equilibrio(under_inicial_jogo, under_atual, minuto_atual, placar_atual)
        
        if projecao:
            df_projecao = pd.DataFrame(projecao)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Under - Projeção Natural:**")
                st.line_chart(df_projecao.set_index('minuto')['under'])
            
            with col2:
                st.write("**Over - Evolução:**")
                st.line_chart(df_projecao.set_index('minuto')['over'])
            
            # Tabela
            st.subheader(f"📋 Projeção Restante - Min {minuto_atual + 1} ao 90")
            
            df_display = df_projecao[['minuto', 'under', 'over']].copy()
            df_display.columns = ['Minuto', 'Under', 'Over']
            
            st.dataframe(df_display, use_container_width=True, height=300)

# Rodapé
st.sidebar.markdown("---")
st.sidebar.markdown("⚽ **Analisador v5.0 - NATURAL**")
st.sidebar.markdown("📊 **Curva Equilibrada**")
st.sidebar.markdown("✅ **Segundo Tempo Ativo**")
