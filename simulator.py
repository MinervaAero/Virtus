import json
from avlwrapper import *
from prototype import *
from performance import *
from stability import *
import numpy as np
import pandas as pd
import time

class Simulator():

    '''
    Classe responsável por criar os cases e realizar as simulações no AVL, tipicamente recebe  geometria no formato Prototype().geometry. Também possui inputs de condições 
    atmosféricas e de parâmetros de casos. Que serão fixos ao longo de toda a otimização.
    Cada indivíduo dessa classe ainda corresponde a uma aeronave, porém a partir daqui inclui suas simulações e parâmetros de simulação.
    '''
    # Cada indivíduo no simulador possui uma geometria sem e com o efeito solo. Isso foi uma solução simples encontrada para incluir todos os coeficientes em um mesmo indivíduo -
    # - para a otimização. Se precisássemos de um caso de transição bastaria simular de novo o efeito solo, mas deslocando o plano de simetria em z para baixo com uma nova vari -
    # - ável da classe protótipo.
    def __init__(self, prototype, prototype_ge, p= 905.5, t= 25, v=10, mach=0.00): #mantido (mas confirmar, talvez tenha que mudar a_trim)

        self.prototype= prototype
        self.prototype_ge= prototype_ge
        self.p= p                      #pressão 
        self.t= t                      #temperatura
        self.v= v                      #velocidade
        self.rho = rho(p=p,t=t)        #densidade do ar
        self.mach = mach               #número de Mach
        self.deflex= {} 
        self.cl= {}
        self.cd= {}
        self.cm= {}
        self.cma= {}
        self.xnp= 0
        self.cnb= {}
        self.cl_ge= {}
        self.cd_ge= {}
        self.a_trim= -20; self.me= -0.2 # Caso não consiga calcular, a pontuação será zerada, mas não dará erro por não ter um valor de a_trim. Algumas simulações dão erro.
        
        # Cl e Cd são armazenados em dicionários com elementos [Ângulo de ataque: Coeficiente]

    # Função que verifica se o estol está ocorrendo ou não, retorna um booleano
    # O método utilizado é a verificação do Clmax para cada secção da asa. Copiando o Xf.
    def check_stall(self, results): #mantido (mas confirmar, não sabemos se precisa adicionar variáveis)

        stall= False
        b_stall=0

        for panel_n in range(int(len(results['a']['StripForces']['Wing']['Yle']))):             # Tinha um /2 aqui, acredito que era um erro
            if results['a']['StripForces']['Wing']['Yle'][panel_n] <= self.prototype.w_baf/2:
                clmax= self.prototype.w_root_clmax

                if results['a']['StripForces']['Wing']['cl'][panel_n] >= clmax:
                    stall= True
                    b_stall= results['a']['StripForces']['Wing']['Yle'][panel_n] / (self.prototype.w_bt/2) #b_stall é o ponto de estol em % da envergadura

                    return stall, b_stall

                else:
                    stall= False

            else:
                af_len= (self.prototype.w_bt - self.prototype.w_baf)/2
                af_len_perc= (results['a']['StripForces']['Wing']['Yle'][panel_n] - self.prototype.w_baf/2)/af_len
                clmax= (af_len_perc)*self.prototype.w_tip_clmax + (1-af_len_perc)*self.prototype.w_root_clmax           # Interpolando os clmáx na região afilada

                if results['a']['StripForces']['Wing']['cl'][panel_n] >= clmax:
                    stall= True
                    b_stall= results['a']['StripForces']['Wing']['Yle'][panel_n] / (self.prototype.w_bt/2) #b_stall é o ponto de estol em % da envergadura
                    
                    return stall, b_stall

                else:
                    stall= False

        return stall, b_stall

    # Cria e roda um caso de angulo de ataque definido e armazena os coeficientes desejados
    def run_a(self, a= 0): #mantido

        #a_case = Case(name='a', alpha=a, density= self.rho, Mach= self.mach, velocity= self.v, X_cg=self.prototype.x_cg, Z_cg=self.prototype.z_cg)

        #A definição de caso abaixo irá retornar a polar trimada, a definição acima retornará a polar sem deflexão de superfícies
        a_case = Case(name='a', alpha=a, density= self.rho, Mach= self.mach, velocity= self.v, X_cg=self.prototype.x_cg, Z_cg=self.prototype.z_cg, elevator=Parameter(name='elevator', constraint='Cm', value=0.0))

        #print(str.format('Calculando coeficientes em alfa = {}',a))

        session = Session(geometry=self.prototype.geometry, cases=[a_case])
        a_results = session.get_results()

        try:
            if not(self.check_stall(a_results)[0]):
                self.deflex[a]= a_results['a']['Totals']['elevator']
                self.cl[a]= a_results['a']['Totals']['CLtot']
                self.cd[a]= a_results['a']['Totals']['CDtot']
                self.cm[a]= a_results['a']['Totals']['Cmtot']
                self.cma[a]= a_results['a']['StabilityDerivatives']['Cma']
                self.cnb[a]= a_results['a']['StabilityDerivatives']['Cnb']

                return a_results
            
            else:
                raise

        except:
            #print('A asa se encontra estolada em alfa=', a, 'graus.')
            print('Estol em', self.check_stall(a_results)[1], '%', 'da envergadura')
            raise

    #LEMBRANDO... EFEITO SOLO NO VLM É CONHECIDO POR SUPERESTIMAÇÃO, PRINCIPALMENTE EM H/C < 0.7
    def run_ge(self): #mantido
        
        print('Calculando coeficientes em efeito solo')

        a_case = Case(name='a', alpha=0, density= self.rho, Mach= self.mach, velocity= self.v, X_cg=self.prototype.x_cg, Z_cg=self.prototype.z_cg)

        session = Session(geometry=self.prototype_ge.geometry, cases=[a_case])
        a_results = session.get_results()

        self.cl_ge[0]= a_results['a']['Totals']['CLtot']
        self.cd_ge[0]= a_results['a']['Totals']['CDtot']

        return a_results

    # Roda uma simulação para cada ângulo de ataque até o estol
    def run_stall(self): #mantido
    
         
        for a in np.arange(5,12,2):
            
            try:
                self.run_a(a)

            except:
                self.a_stall= a-1
                self.clmax= self.cl[a-1]
                print('Angulo de estol entre=', a-1,'e', a, 'graus')
                break

        for a in np.arange(12,31,1):
            
            try:
                self.run_a(a)

            except:
                self.a_stall= a-1
                self.clmax= self.cl[a-1]
                print('Angulo de estol entre=', a-1,'e', a, 'graus')
                break
    
    # Roda uma simulação com o avião trimmado com momento zerado, pra encontrar o ângulo de trimmagem e a margem estática
    def run_trim(self):

        trimmed= Case(name='trimmed', alpha=Parameter(name='alpha', constraint='Cm',value=0.0), X_cg=self.prototype.x_cg, Z_cg=self.prototype.z_cg)
        session=Session(geometry= self.prototype.geometry, cases=[trimmed])
        trim_results = session.get_results()

        self.a_trim= trim_results['trimmed']['Totals']['Alpha']
        self.xnp= trim_results['trimmed']['StabilityDerivatives']['Xnp']
        self.me= me(self.xnp, self.prototype.x_cg, self.prototype.mac)

    # Método que escreve os resultados mais recentes em um arquivo json nomeado
    def write_results(self, filename):
        with open(filename+'.json', 'w') as f:
            f.write(json.dumps(self.results))
    
    # Método que imprime os coeficientes armazenados
    def print_coeffs(self): #mantido (mas confirmar)

        aero_coeffs= pd.DataFrame([self.cl, self.cd, self.cm, self.deflex], index= ['CL','CD','CM','Prof'])
        aero_coeffs= aero_coeffs.T

        print('--------------OUTPUTS-----------------\n')
        print('--------------Aerodinamica-----------------')
        print('Coeficientes aerodinamicos:\n', aero_coeffs, sep='')
        print('CL em corrida=', self.cl_ge[0])
        print('CD em corrida=', self.cd_ge[0])
        print('Envergadura=', round(self.prototype.w_bt,3),'m')
        print('Transicao=', round(self.prototype.w_baf/self.prototype.w_bt,3)*100,'%','da envergadura')
        print('Area alar=', round(self.prototype.s_ref,3), 'm^2')
        print('AR=', round(self.prototype.ar,2))
        print('AR do EH=', round(self.prototype.eh_ar,2))
        print('M.A.C.=', round(self.prototype.mac,3), 'm')
        print('--------------Controle e Estabilidade-----------------')
        print('VHT=', round(self.prototype.vht,4))
        print('VVT=', round(self.prototype.vvt,4))
        print('X_CG=', round(self.prototype.x_cg_p,3), '% ', 'da corda da asa')
        print('Z_CG=', round(self.prototype.z_cg,3), 'm do chao')
        print('CG=', round(self.prototype.low_cg,3), 'm abaixo da asa')
        print('Angulo de trimagem=', round(self.a_trim,2), 'graus')
        print('Margem Estatica=', round(self.me,3))
        print('--------------Restricoes-----------------')
        print('Altura do EH com relacao a asa=', round(self.prototype.eh_z_const,3), 'm')
        print('--------------Estruturas-----------------')
        print('Peso Vazio=', round(self.prototype.pv,3),'kg')
        
    # Método que realiza a simulação e pontuação da aeronave. No caso de qualquer erro, a pontuação do indivíduo é zerada
    def scorer(self):

        try:
            self.run_a(0)
            print('CASO ALFA 0 CONCLUIDO')
        except:
            print('FALHA NA SIMULACAO DE ALFA 0')
            self.score=0

        try:
            self.run_ge()
            print('CASO EFEITO SOLO CONCLUIDO')
        except:
            print('FALHA NA SIMULACAO EM EFEITO SOLO')
            self.score=0

        try:
            self.run_stall()   
            print('CASO ESTOL CONCLUIDO')  
        except:
            print('FALHA NA SIMULACAO ATE O ESTOL')
            self.score=0

        try:
            self.run_trim()   
            print('CASO TRIMADO CONCLUIDO')  
        except:
            print('FALHA NA SIMULACAO DE TRIMAGEM')
            self.score=0
            a_trim= 0
        
        try:
            #A otimização busca um mínimo, portanto a nossa pontuação é espelhada aqui 
            self.mtow= mtow(self.p, self.t, self.v, self.prototype.pv, self.prototype.s_ref, self.cl_ge[0], self.clmax, self.cd_ge[0], self.cd[0], self.prototype.pot, g= 9.81, mu= 0.03, n= 1.2, gamma= 0)
            print('MTOW CALCULADO COM SUCESSO') #analisar de onde puxa a potencia
            self.prototype.m= self.mtow

            self.cp= self.mtow - self.prototype.pv

            self.score= self.cp

            self.print_coeffs()                                    # Printa os coeficientes desejados após a otimização
            
            print('--------------Desempenho-----------------')
            print('MTOW=', round(self.mtow,3),'kg')
            print('########## Carga paga=', round(self.cp,3),'kg ##########')
            #print('v_decol=', round(1.2*v_estol(self.p, self.t, self.prototype.m, self.prototype.s_ref, self.clmax, g=9.81),3))
            
            
        except: 
            print('FALHA NA SIMULACAO DE MTOW')
            self.score=0
            self.cp=0
    
        
        ##### PENALIDADES MANUAIS #####

        a_trim_pen= 0
        x_cg_p_pen= 0
    
        if self.a_trim > a_trim_max:
            a_trim_pen= 2+ 10*(self.a_trim - a_trim_max)

        if self.a_trim < a_trim_min:
            a_trim_pen= 2+ 10*(a_trim_min - self.a_trim)

        if self.prototype.x_cg_p > 0.35:
            a_trim_pen= 2+ 10*(self.prototype.x_cg_p - 0.35)

        if self.prototype.x_cg_p < 0.25:
            a_trim_pen= 2+ 10*(0.25 - self.prototype.x_cg_p)

        pen= a_trim_pen + x_cg_p_pen

        self.score= self.score - pen
        
        

        return self.score
if __name__ == '__main__':
        banana = Prototype( w_bt= 3.2321286257332065, w_baf= 0.9, w_cr= 0.45, w_ci= 0.8547042296684797, w_ct= 0.8, w_z= 0.18, w_inc= -0.3960870755918585, w_wo= 0.0, w_d= 2.1132179687299235, eh_b= 0.6197954432211882, eh_cr= 0.24309488336263088, eh_ct= 0.8, eh_inc= -2.0, ev_b= 0.4, ev_ct= 0.7900185499329802, eh_x= 1.3699514929079597, eh_z= 0.3, motor_x= -0.4, ge= False)
        banana_ge = Prototype( w_bt= 3.2321286257332065, w_baf= 0.9, w_cr= 0.45, w_ci= 0.8547042296684797, w_ct= 0.8, w_z= 0.18, w_inc= -0.3960870755918585, w_wo= 0.0, w_d= 2.1132179687299235, eh_b= 0.6197954432211882, eh_cr= 0.24309488336263088, eh_ct= 0.8, eh_inc= -2.0, ev_b= 0.4, ev_ct= 0.7900185499329802, eh_x= 1.3699514929079597, eh_z= 0.3, motor_x= -0.4, ge= True)
        
        a0 = Case(name='a0', alpha=0, X_cg= banana.x_cg, Z_cg= banana.z_cg)
    
        session=Session(geometry=banana.geometry,cases=[a0])

        session._run_analysis


        results= session.get_results()

        with open('./out.json', 'w') as f:
           f.write(json.dumps(results))
        

        bananasimulation = Simulator(banana, banana_ge, p= 905.5, t= 25, v=10, mach=0.00)
        bananasimulation.scorer()
        bananasimulation.run_a(0)
        
 