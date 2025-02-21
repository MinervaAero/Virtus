import openmdao.api as om
from prototype import *
from simulator import *
from avlwrapper import *	


class Individual(om.ExplicitComponent):
    '''
    Classe responsável por formatar e simular o score de um indivíduo da classe Simulator() em um componente para a otimização no openMDAO
    '''
    # Definição de todas as variáveis de design a serem otimizadas
    def setup(self):
        self.add_input('w_bt', val= 3.0)
        self.add_input('w_baf', val= 0.2)
        self.add_input('w_cr', val= 0.40)
        self.add_input('w_ci', val= 0.90)         #adicionado
        self.add_input('w_ct', val= 0.87)
        self.add_input('w_z', val= 0.21)
        self.add_input('w_inc', val= 0)
        self.add_input('w_wo', val= 0)            #adicionado
        self.add_input('w_d', val= 1.4)           #adicionado
        self.add_input('eh_b', val= 0.74)
        self.add_input('eh_cr', val= 0.26)        #adicionado
        self.add_input('eh_ct', val= 0.90)        #adicionado
        self.add_input('eh_inc', val= -1.19)
        self.add_input('ev_b', val= 0.32)
        self.add_input('ev_ct', val= 0.83)        #adicionado
        self.add_input('eh_x', val= 1.051)
        self.add_input('eh_z', val= 0.4)
        self.add_input('motor_x', val= -0.218)
        #self.add_input('pot', val= 600)           #alterado

        # Os outputs incluem a pontuação e possíveis restrições calculadas internamente em outro código
        self.add_output('score', val= 7.7)
        self.add_output('cp', val= 7.7)
        self.add_output('vht', val= 0.5)
        self.add_output('vvt', val= 0.04)
        #self.add_output('cm0', val= 0.05)
        self.add_output('a_trim', val= 3)
        self.add_output('me', val= 0.1)
        self.add_output('ar', val= 5.5)
        self.add_output('eh_ar', val= 4.0)
        #self.add_output('ev_ar', val= 4.0)       #adicionado (NÃO TEMOS CERTEZA SE PRECISA)
        #self.add_output('h_const', val= 0.6)
        self.add_output('eh_z_const', val= 0.06)
        self.add_output('low_cg', val= 0.02)
        self.add_output('x_cg_p', val= 0.35)

    # Aqui definimos o que vamos rodar para cada indivíduo
    def compute(self,inputs,outputs):
        # Antes, precisamos converter os inputs do openmdao (arrays) em floats para as classes e funções dos outros módulos
        w_bt= float(inputs['w_bt'])
        w_baf= float(inputs['w_baf'])
        w_cr= float(inputs['w_cr'])
        w_ci= float(inputs['w_ci'])         #adicionado
        w_ct= float(inputs['w_ct'])
        w_z= float(inputs['w_z'])
        w_inc= float(inputs['w_inc'])
        w_wo= float(inputs['w_wo'])         #adicionado
        w_d= float(inputs['w_d'])           #adicionado
        eh_b= float(inputs['eh_b'])
        eh_cr= float(inputs['eh_cr'])       #adicionado
        eh_ct= float(inputs['eh_ct'])       #adicionado
        eh_inc= float(inputs['eh_inc'])
        ev_b= float(inputs['ev_b'])
        ev_ct= float(inputs['ev_ct'])       #adicionado
        eh_x= float(inputs['eh_x'])
        eh_z= float(inputs['eh_z'])
        motor_x= float(inputs['motor_x'])
        #pot= float(inputs['pot'])


        # Construção dos indivíduos. Para facilitar, está sendo construindo um indivíduo com e o outro sem efeito solo
        prototype= Prototype(w_bt, w_baf, w_cr, w_ci, w_ct, w_z, w_inc, w_wo, w_d, eh_b, eh_cr, eh_ct, eh_inc, eh_x, eh_z, ev_ct, ev_b, motor_x, motor_z= 0.30, ge= False)   #alterado (confirmar)
        prototype_ge= Prototype(w_bt, w_baf, w_cr, w_ci, w_ct, w_z, w_inc, w_wo, w_d, eh_b, eh_cr, eh_ct, eh_inc, eh_x, eh_z, ev_ct, ev_b, motor_x, motor_z= 0.30, ge= True) #alterado (confirmar)
        simulator= Simulator(prototype, prototype_ge)

        # Rodando a pontuação de cada indivíduo
        score= simulator.scorer()
        
        # Definindo os outputs dessa computação. Nesse caso, todos os outputs do indivíduo saem daqui mesmo 
        #verificar necessidade de novos parâmetros
        outputs['score'] = score
        outputs['vht'] = prototype.vht
        outputs['vvt'] = prototype.vvt
        #outputs['cm0'] = simulator.cm[0]
        outputs['a_trim'] = simulator.a_trim
        outputs['me'] = simulator.me
        #outputs['h_const']= prototype.h_const
        outputs['eh_z_const']= prototype.eh_z_const
        outputs['ar']= prototype.ar
        outputs['eh_ar']= prototype.eh_ar
        outputs['low_cg']= prototype.low_cg
        outputs['x_cg_p']= prototype.x_cg_p
        outputs['cp']= simulator.cp
