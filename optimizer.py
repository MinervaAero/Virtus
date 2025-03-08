
import openmdao.api as om
from prototype import *
from simulator import *
from individual import *
from performance import *

'''
Programa de otimização, que cria e avalia indivíduos da classe Individual(), otimizando-os a partir do driver escolhido, futuramente pode haver a implementação de outros módulos
e a necessidade da inclusão de ciclos
'''
#Criação do problema
prob= om.Problem()

#Definição dos subsistemas
individual_inputs= ['w_bt', 'w_baf', 'w_cr', 'w_ci', 'w_ct', 'w_z', 'w_inc', 'w_wo', 'w_d', 'eh_b', 'eh_cr', 'eh_ct', 'eh_inc', 'ev_b', 'ev_ct', 'eh_x', 'eh_z', 'motor_x']
individual_outputs= ['score','cp', 'vht', 'vvt', 'a_trim', 'me', 'ar', 'eh_ar', 'low_cg', 'eh_z_const', 'x_cg_p']

#Subsistema de avaliação
prob.model.add_subsystem('individual_scorer', Individual(), promotes_inputs= individual_inputs)

prob.model.set_input_defaults('w_bt', 2.7)
prob.model.set_input_defaults('w_baf', 0.5)
prob.model.set_input_defaults('w_cr', 0.4)
prob.model.set_input_defaults('w_ci', 0.90) #adicionado
prob.model.set_input_defaults('w_ct', 0.87)
prob.model.set_input_defaults('w_z', 0.20)
prob.model.set_input_defaults('w_inc', 0.0)
prob.model.set_input_defaults('w_wo', 0.0)
prob.model.set_input_defaults('w_d', 1.4)
prob.model.set_input_defaults('eh_b', 0.7)
prob.model.set_input_defaults('eh_cr', 0.25) #adicionado
prob.model.set_input_defaults('eh_ct', 0.87) #adicionado
prob.model.set_input_defaults('eh_inc', 0)
prob.model.set_input_defaults('ev_b', 0.30)
prob.model.set_input_defaults('ev_ct', 0.8) #adicionado
prob.model.set_input_defaults('eh_x', 1.2)
prob.model.set_input_defaults('eh_z', 0.4)
prob.model.set_input_defaults('motor_x', -0.2)
#prob.model.set_input_defaults('pot', 600)     #alterado

#Setup do driver de otimização diferencial

prob.driver = om.DifferentialEvolutionDriver()
prob.driver.options['debug_print']= ['desvars']           # Apenas pra debug no log
prob.driver.options['pop_size']= 33                       # Muito importante um número bom pra explorar todo o espaço de design. Quanto mais variável maior precisa ser a pop.
prob.driver.options['penalty_parameter']= 20.0            # Necessário para controlar a violação das restrições
prob.driver.options['penalty_exponent']= 1.0
prob.driver.options['run_parallel']= False                # Só funciona se conseguir fazer o programa rodar no mpi, mais fácil pelo wsl

'''
#Setup do driver de algoritmo genetico simples
prob.driver = om.SimpleGADriver()
prob.driver.options['debug_print']= ['desvars']#, 'nl_cons', 'totals']    # Apenas pra debug no log
prob.driver.options['pop_size']= 33                                     # Muito importante um número bom pra explorar todo o espaço de design. Quanto mais variáveis maior precisa ser a pop.
prob.driver.options['bits'] = {'w_cr': 4, 'w_ct': 5, 'w_z': 4, 'w_inc': 6, 'eh_b': 6, 'eh_c': 4, 'eh_inc': 6, 'ev_b': 4, 'eh_x': 6, 'eh_z': 4, 'motor_x': 5}
prob.driver.options['max_gen'] = 120
prob.driver.options['penalty_parameter']= 50                          # Necessário ajuste para controlar a violação das restrições
prob.driver.options['penalty_exponent']= 1.0
prob.driver.options['run_parallel']= False                            # Só funciona se conseguir fazer o programa rodar no mpi, mais fácil pelo wsl
prob.driver.options['Pc']= 0.6
prob.driver.options['Pm']= 0.025
prob.driver.options['elitism']= True
'''

#Adição de um recorder para guardar o histórico da otimização e possibilitar a visualização
prob.driver.add_recorder(om.SqliteRecorder("./runCSfoil600.db"))
prob.driver.recording_options['includes'] = ['*']
prob.driver.recording_options['record_objectives'] = True
prob.driver.recording_options['record_constraints'] = True
prob.driver.recording_options['record_desvars'] = True

# Adicionando todas as variáveis de design

prob.model.add_design_var('w_bt', lower= 2.5, upper= 3.5)       #alterado
prob.model.add_design_var('w_baf', lower= 0.1, upper= 0.9)      #alterado
prob.model.add_design_var('w_cr', lower= 0.25, upper= 0.52)     #alterado
prob.model.add_design_var('w_ci', lower= 0.85, upper= 0.95)     #adicionado/alterado
prob.model.add_design_var('w_ct', lower= 0.8, upper= 0.95)      #alterado
prob.model.add_design_var('w_z', lower= 0.18, upper= 0.24)      #mantido
prob.model.add_design_var('w_inc', lower= -2, upper= 4)         #alterado
prob.model.add_design_var('w_wo', lower= -3, upper= 0)          #adicionado
prob.model.add_design_var('w_d', lower= 1, upper= 3)            #adicionado
prob.model.add_design_var('eh_b', lower= 0.6, upper= 0.8)       #alterado
prob.model.add_design_var('eh_cr', lower= 0.20, upper= 0.30)    #adicionado
prob.model.add_design_var('eh_ct', lower= 0.80, upper= 0.95)    #adicionado
prob.model.add_design_var('eh_inc', lower= -2.0, upper= 3.0)    #alterado
prob.model.add_design_var('eh_x', lower= 1.0, upper= 1.4)       #alterado
prob.model.add_design_var('eh_z', lower= 0.3, upper= 0.5)       #alterado
prob.model.add_design_var('ev_b', lower= 0.25, upper= 0.4)      #alterado
prob.model.add_design_var('ev_ct', lower= 0.70, upper= 0.90)    #adicionado/a ser alterado
prob.model.add_design_var('motor_x', lower= -0.4, upper= -0.15) #mantido
#prob.model.add_design_var('pot', lower= 600, upper= 600)        #alterado

prob.model.add_objective('individual_scorer.score', scaler= -1) #-1 para maximizar o valor do score

# Adicionando as restrições e seus limites superiores e inferiores.
# Ele não zera as pontuações dos indivíduos que violam as restrições, apenas penaliza. As configurações de penalização influenciam bastante... Principalmente se ele encontrar -
# - alguma falha do avl (ex.: uma asa com a ponta entrando nela de novo dava um cl absurdamente alto e ele otimizava nessa direção nas primeiras versões)
# Sim, daria pra zerar a pontuação de qualquer indivíduo que violasse alguma dessas restrições, só que isso é bem ineficiente (testado)

prob.model.add_constraint('individual_scorer.ar', lower= 5.0, scaler= 1)
prob.model.add_constraint('individual_scorer.eh_ar', upper= 4.8, scaler= 1)
prob.model.add_constraint('individual_scorer.vht', lower= vht_min, upper= vht_max, scaler= 1)
prob.model.add_constraint('individual_scorer.vvt', lower= vvt_min, upper= vvt_max, scaler= 1)
#prob.model.add_constraint('individual_scorer.cm0', lower= cm0_min, scaler= 0)
prob.model.add_constraint('individual_scorer.a_trim', lower= a_trim_min, upper= a_trim_max, scaler= 0.0) # 10 anteriormente
prob.model.add_constraint('individual_scorer.me', lower= me_min, upper= me_max, scaler= 1)
prob.model.add_constraint('individual_scorer.low_cg', lower= -0.03, scaler= 1)
#prob.model.add_constraint('individual_scorer.h_const', upper= 0.60, scaler= 1)
prob.model.add_constraint('individual_scorer.eh_z_const', lower= 0.05, scaler= 1)
prob.model.add_constraint('individual_scorer.x_cg_p', lower= 0.25, upper= 0.34, scaler= 0.0) # 100 anteriormente

# Settando e rodando o driver
prob.setup()

prob.run_driver()

# Incluindo um report em html ao fim da otimização. Não parece tão útil não.
# Se parar o programa com um CTRL+C nem mostra
#prob.driver.scaling_report()