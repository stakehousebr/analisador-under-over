import math
import pandas as pd
from datetime import datetime

# ====================================================================
# 📋 SEÇÃO DE CONFIGURAÇÃO - PREENCHA AQUI SEUS DADOS
# ====================================================================

# ❓ CONFIGURAÇÃO INICIAL
JOGO_COMECOU = True  # True = Jogo em andamento | False = Jogo não começou

# 📊 DADOS PARA JOGO NÃO COMEÇADO (se JOGO_COMECOU = False)
UNDER_INICIAL = 42.0
OVER_INICIAL = 1.02

# 📊 DADOS PARA JOGO EM ANDAMENTO (se JOGO_COMECOU = True)
PLACAR_ATUAL = "2x0"           # Exemplo: "0x0", "1x1", "2x0"
UNDER_INICIAL_JOGO = 42.0      # Odd inicial do Under
OVER_INICIAL_JOGO = 1.02       # Odd inicial do Over  
UNDER_ATUAL = 14.0             # Odd atual do Under
OVER_ATUAL = 1.07              # Odd atual do Over
MINUTO_ATUAL = 30              # Minuto atual da partida

# ====================================================================
# 🔧 CÓDIGO PRINCIPAL - NÃO MEXER AQUI
# ====================================================================

class AnalisadorApostasUnderOver:
    def __init__(self):
        """Inicializa o analisador com curva de equilíbrio baseada em dados reais"""
        # Pontos-chave da curva de equilíbrio (baseada na média das duas amostras)
        self.pontos_equilibrio = {
            1: 42.0,   # Minuto 1
            15: 28.0,  # Meio do primeiro tempo
            30: 14.0,  # Final do primeiro tempo
            35: 12.4,
            40: 10.8,
            42: 10.0,
            45: 9.1,
            46: 8.5,   # Início segundo tempo
            50: 7.8,
            55: 6.2,
            60: 4.5,   # Meio segundo tempo
            65: 3.95,
            70: 3.4,
            75: 2.9,
            80: 2.5,
            85: 2.1,
            90: 1.50   # Final
        }
        
        self.historico_convergencia = {
            # Dados reais coletados e ajustados para equilíbrio
            6.4: 1.25,
            10.0: 1.25,
            19.5: 1.29,
            22.0: 1.39,
            27.0: 1.22,
            36.0: 1.47,  # Amostra real 1
            39.0: 1.50,  # Ponto de equilíbrio
            42.0: 1.54   # Amostra real 2
        }
    
    def calcular_under_final_esperado(self, odd_inicial):
        """Calcula o Under final com lógica de equilíbrio"""
        if odd_inicial >= 40:
            return 1.48 + (odd_inicial - 40) * 0.03  # Mais suave
        elif odd_inicial >= 35:
            return 1.45 + (odd_inicial - 35) * 0.02
        elif odd_inicial >= 25:
            return 1.30 + (odd_inicial - 25) * 0.015
        elif odd_inicial >= 19:
            return 1.25 + (odd_inicial - 19) * 0.008
        elif odd_inicial >= 10:
            return 1.15 + (odd_inicial - 10) * 0.012
        else:
            return 1.25 + (8 - odd_inicial) * 0.01
    
    def calcular_over_baseado_no_under(self, under_atual):
        """Calcula o Over baseado matematicamente no Under"""
        try:
            prob_under = 1 / under_atual
            prob_over = 1 - prob_under
            
            if prob_over <= 0.001:
                return 999.0
            
            over_atual = 1 / prob_over
            return over_atual
            
        except (ZeroDivisionError, ValueError):
            return 999.0
    
    def interpolar_ponto(self, minuto, pontos_ref):
        """Interpola between reference points para criar curva suave"""
        if minuto in pontos_ref:
            return pontos_ref[minuto]
        
        # Encontra os pontos antes e depois
        minutos_sorted = sorted(pontos_ref.keys())
        
        if minuto < minutos_sorted[0]:
            return pontos_ref[minutos_sorted[0]]
        if minuto > minutos_sorted[-1]:
            return pontos_ref[minutos_sorted[-1]]
        
        # Interpolação linear entre pontos
        for i in range(len(minutos_sorted) - 1):
            min1, min2 = minutos_sorted[i], minutos_sorted[i + 1]
            if min1 <= minuto <= min2:
                val1, val2 = pontos_ref[min1], pontos_ref[min2]
                # Interpolação linear
                fator = (minuto - min1) / (min2 - min1)
                return val1 + (val2 - val1) * fator
        
        return pontos_ref[minutos_sorted[-1]]
    
    def gerar_curva_equilibrio_90min(self, under_inicial, over_inicial):
        """Gera curva baseada no padrão de equilíbrio real"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Ajusta pontos de referência baseado na odd inicial
        fator_ajuste = under_inicial / 39.0  # 39 é nossa referência média
        pontos_ajustados = {}
        
        for minuto, valor in self.pontos_equilibrio.items():
            if minuto == 90:
                pontos_ajustados[minuto] = under_final
            else:
                # Ajusta proporcionalmente
                valor_ajustado = valor * fator_ajuste
                # Suaviza o ajuste para evitar distorções extremas
                if valor_ajustado > under_inicial:
                    valor_ajustado = under_inicial * (0.7 + 0.3 * (valor / max(self.pontos_equilibrio.values())))
                pontos_ajustados[minuto] = valor_ajustado
        
        curva = []
        
        for minuto in range(1, 91):
            under_atual = self.interpolar_ponto(minuto, pontos_ajustados)
            over_atual = self.calcular_over_baseado_no_under(under_atual)
            
            curva.append({
                'minuto': minuto,
                'under': round(under_atual, 2),
                'over': round(over_atual, 3)
            })
        
        return curva
    
    def exibir_tabela_completa(self, curva):
        """Exibe a tabela completa minuto a minuto"""
        print("\n📊 TABELA COMPLETA MINUTO A MINUTO")
        print("=" * 75)
        print("| Min | Under | Over   | Min | Under | Over   | Min | Under | Over   |")
        print("|-----|-------|--------|-----|-------|--------|-----|-------|--------|")
        
        for i in range(0, 30):
            linha1 = curva[i]
            linha2 = curva[i + 30] if i + 30 < 90 else {'minuto': '', 'under': '', 'over': ''}
            linha3 = curva[i + 60] if i + 60 < 90 else {'minuto': '', 'under': '', 'over': ''}
            
            over1 = f"{linha1['over']:6.3f}" if linha1['over'] < 10 else f"{linha1['over']:6.2f}"
            over2 = f"{linha2.get('over', 0):6.3f}" if linha2.get('over', 0) and linha2.get('over', 0) < 10 else f"{linha2.get('over', 0):6.2f}"
            over3 = f"{linha3.get('over', 0):6.3f}" if linha3.get('over', 0) and linha3.get('over', 0) < 10 else f"{linha3.get('over', 0):6.2f}"
            
            min1 = f"{linha1['minuto']:2d}"
            min2 = f"{linha2.get('minuto', ''):2s}" if linha2.get('minuto') else "  "
            min3 = f"{linha3.get('minuto', ''):2s}" if linha3.get('minuto') else "  "
            
            under2 = f"{linha2.get('under', 0):5.2f}" if linha2.get('under') else "     "
            under3 = f"{linha3.get('under', 0):5.2f}" if linha3.get('under') else "     "
            
            print(f"| {min1}  | {linha1['under']:5.2f} | {over1} | " +
                  f"{min2}  | {under2} | {over2} | " +
                  f"{min3}  | {under3} | {over3} |")
        
        print("=" * 75)
    
    def projetar_restante_equilibrio(self, under_inicial, under_atual, minuto_atual, placar):
        """Projeta o restante usando curva de equilíbrio"""
        under_final = self.calcular_under_final_esperado(under_inicial)
        
        # Cria pontos de referência do minuto atual até o final
        pontos_restantes = {}
        
        # Ponto atual
        pontos_restantes[minuto_atual] = under_atual
        
        # Pontos de referência ajustados proporcionalmente
        fator_ajuste_atual = under_atual / self.interpolar_ponto(minuto_atual, self.pontos_equilibrio)
        
        for minuto in range(minuto_atual + 1, 91):
            if minuto == 90:
                pontos_restantes[minuto] = under_final
            else:
                valor_ref = self.interpolar_ponto(minuto, self.pontos_equilibrio)
                # Ajusta baseado na posição atual vs referência
                if minuto <= minuto_atual + 15:  # Próximos 15 minutos
                    pontos_restantes[minuto] = valor_ref * fator_ajuste_atual
                else:  # Convergência gradual para o padrão
                    peso_ajuste = (90 - minuto) / (90 - minuto_atual - 15)
                    pontos_restantes[minuto] = valor_ref * (1 + (fator_ajuste_atual - 1) * peso_ajuste * 0.5)
        
        projecao = []
        
        for i in range(minuto_atual + 1, 91):
            under_projetado = self.interpolar_ponto(i, pontos_restantes)
            over_projetado = self.calcular_over_baseado_no_under(under_projetado)
            
            projecao.append({
                'minuto': i,
                'under': round(under_projetado, 2),
                'over': round(over_projetado, 3)
            })
        
        return projecao
    
    def analisar_divergencia(self, under_atual_real, under_esperado, minuto):
        """Analisa divergência entre odd real e esperada"""
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
                queda_percent = ((odd_entrada - odd_10min_depois) / odd_entrada) * 100
                
                if 2.5 <= odd_entrada <= 35.0 and queda_percent >= 8:
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
                
                if over_final > odd_over:
                    risco_correcao = ((over_final - odd_over) / odd_over) * 100
                else:
                    risco_correcao = 0
                
                if odd_over >= 1.1 and risco_correcao <= 60:
                    melhores_entradas.append({
                        'minuto': i + 1,
                        'odd_entrada': odd_over,
                        'under_atual': under_atual,
                        'risco_correcao': round(risco_correcao, 1),
                        'estabilidade': 'Alta' if risco_correcao < 20 else 'Média'
                    })
        
        return sorted(melhores_entradas, key=lambda x: x['risco_correcao'])[:3]

def executar_analise():
    """Executa a análise com base nas configurações"""
    analisador = AnalisadorApostasUnderOver()
    
    print("🎯" + "="*60)
    print("      ANALISADOR PROFISSIONAL UNDER/OVER v3.0")
    print("          🔄 CURVA DE EQUILÍBRIO REAL")
    print("="*63 + "🎯")
    print()
    
    if not JOGO_COMECOU:
        print("📊 MODO: PROJEÇÃO COMPLETA (90 MINUTOS)")
        print("=" * 50)
        print(f"📋 Dados: Under {UNDER_INICIAL} | Over {OVER_INICIAL}")
        print()
        
        curva = analisador.gerar_curva_equilibrio_90min(UNDER_INICIAL, OVER_INICIAL)
        
        print("📈 PROJEÇÃO COMPLETA")
        print("-" * 30)  
        print(f"Under: {UNDER_INICIAL} → {curva[89]['under']}")
        print(f"Over: {OVER_INICIAL} → {curva[89]['over']}")
        print()
        
        print("⏰ EVOLUÇÃO DA PARTIDA:")
        print("-" * 25)
        marcos = [14, 29, 44, 59, 74, 89]
        
        for i in marcos:
            ponto = curva[i]
            over_formatado = f"{ponto['over']:6.3f}" if ponto['over'] < 10 else f"{ponto['over']:6.2f}"
            print(f"Min {ponto['minuto']:2d}: Under {ponto['under']:5.2f} | Over {over_formatado}")
        
        analisador.exibir_tabela_completa(curva)
        
        print("\n🎯 ESTRATÉGIAS DE ENTRADA")
        print("=" * 35)
        
        melhores_under = analisador.analisar_melhor_entrada_under(curva)
        print("\n💎 TOP 3 ENTRADAS UNDER:")
        if melhores_under:
            for i, entrada in enumerate(melhores_under, 1):
                print(f"{i}. Min {entrada['minuto']:2d}: {entrada['odd_entrada']:5.2f} → {entrada['odd_apos_10min']:5.2f} ({entrada['potencial_lucro']})")
        else:
            print("❌ Nenhuma entrada Under favorável identificada")
        
        melhores_over = analisador.analisar_melhor_entrada_over(curva)
        print("\n🚀 TOP 3 ENTRADAS OVER:")
        if melhores_over:
            for i, entrada in enumerate(melhores_over, 1):
                over_formatado = f"{entrada['odd_entrada']:6.3f}" if entrada['odd_entrada'] < 10 else f"{entrada['odd_entrada']:6.2f}"
                print(f"{i}. Min {entrada['minuto']:2d}: {over_formatado} (Risco: {entrada['risco_correcao']}%)")
        else:
            print("❌ Nenhuma entrada Over favorável identificada")
    
    else:
        print("📊 MODO: JOGO EM ANDAMENTO")
        print("=" * 40)
        print(f"📋 Dados: {PLACAR_ATUAL} | Min {MINUTO_ATUAL}")
        print(f"🎯 Under: {UNDER_INICIAL_JOGO} → {UNDER_ATUAL}")
        print(f"🎯 Over: {OVER_INICIAL_JOGO} → {OVER_ATUAL}")
        print()
        
        # Gera curva completa para análise
        curva = analisador.gerar_curva_equilibrio_90min(UNDER_INICIAL_JOGO, OVER_INICIAL_JOGO)
        under_esperado = curva[MINUTO_ATUAL - 1]['under']
        over_esperado = curva[MINUTO_ATUAL - 1]['over']
        
        # Análise de divergência
        divergencia = analisador.analisar_divergencia(UNDER_ATUAL, under_esperado, MINUTO_ATUAL)
        
        print("🔍 ANÁLISE DE DIVERGÊNCIA")
        print("=" * 35)
        print(f"Under Esperado: {under_esperado:.2f}")
        print(f"Under Atual: {UNDER_ATUAL}")
        print(f"Over Esperado: {over_esperado:.3f}")
        print(f"Over Atual: {OVER_ATUAL}")
        print(f"Divergência Under: {divergencia['divergencia_percent']:+.1f}%")
        print()
        print(f"Status: {divergencia['status']}")
        print(f"Explicação: {divergencia['explicacao']}")
        print(f"Recomendação: {divergencia['recomendacao']}")
        print(f"Nível de Risco: {divergencia['risco']}")
        print()
        
        # Análise de ritmo
        taxa_queda = analisador.calcular_taxa_queda(UNDER_INICIAL_JOGO, UNDER_ATUAL, MINUTO_ATUAL)
        ritmo, descricao = analisador.classificar_ritmo(taxa_queda)
        
        print("📊 ANÁLISE DE RITMO")
        print("=" * 25)
        print(f"Taxa de queda: {taxa_queda:.4f}/min")
        print(f"Perfil: {ritmo}")
        print(f"Descrição: {descricao}")
        print()
        
        # Projeção final
        under_final = analisador.calcular_under_final_esperado(UNDER_INICIAL_JOGO)
        over_final = analisador.calcular_over_baseado_no_under(under_final)
        queda_restante = ((UNDER_ATUAL - under_final) / UNDER_ATUAL) * 100
        
        print("🎯 PROJEÇÃO FINAL")
        print("=" * 20)
        print(f"Under final esperado: {under_final:.2f}")
        print(f"Over final esperado: {over_final:.3f}")
        print(f"Queda restante Under: {queda_restante:.1f}%")
        
        if queda_restante > 25:
            potencial = "🔥 MUITO ALTO"
        elif queda_restante > 15:
            potencial = "💰 ALTO"
        elif queda_restante > 8:
            potencial = "⚖️ MÉDIO"
        else:
            potencial = "⚠️ BAIXO"
        
        print(f"Potencial Under: {potencial}")
        
        # TABELA MINUTO A MINUTO DO RESTANTE
        print(f"\n📊 PROJEÇÃO RESTANTE MINUTO A MINUTO")
        print("=" * 45)
        projecao = analisador.projetar_restante_equilibrio(UNDER_INICIAL_JOGO, UNDER_ATUAL, MINUTO_ATUAL, PLACAR_ATUAL)
        
        print("| Min | Under | Over   |")
        print("|-----|-------|--------|")
        for ponto in projecao:
            over_formatado = f"{ponto['over']:6.3f}" if ponto['over'] < 10 else f"{ponto['over']:6.2f}"
            print(f"| {ponto['minuto']:2d}  | {ponto['under']:5.2f} | {over_formatado} |")
        
        print("=" * 45)
    
    print(f"\n{'='*63}")
    print("✅ Análise concluída com Curva de Equilíbrio! 🍀")
    print(f"{'='*63}")

# Executar análise
if __name__ == "__main__":
    executar_analise()
