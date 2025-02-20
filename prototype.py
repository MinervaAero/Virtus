from avlwrapper import *
from mass import *
from support import *
from math import *

def h_const(ev_z,ev_b): #mantido
    '''
    Função que calcula o valor relacionado à restrição geométrica

    w_bt[m],ev_z[m],ev_b[m] -> g_const[m]
    '''
    return ev_z+ev_b

def s_ref(w_cr, w_ci, w_baf,w_ct,w_bt): #alterado
    '''
    Função que calcula a área alar de uma asa com dois afilamentos
    
    Se atentar a calculos futuros em simulações simétricas (meia aeronave)

    w_cr[m], w_ci[m], w_baf[m],w_ct[m],w_bt[m] -> s_ref[m^2]

    '''
    return (((w_cr+w_ci)*w_baf/2) + ((w_ci+w_ct)/2)*(w_bt-w_baf))

def c_med(s_ref,w_bt): #mantido
    '''
    Função que calcula a corda média de uma asa trapezoidal

    s_ref[m],w_bt[m] -> c_med[m]
    '''
    return s_ref/w_bt

def z_d(w_b,w_d): 
    '''
    Função que calcula a altura de uma secção de uma superfície sustentadora em uma determinada envergadura dado o seu ângulo de diedro. Quando o mesmo se inicia da raíz

    w_b[m],w_d[m] -> w_z[m]
    '''
    w_z= w_b*tan(radians(w_d))
    
    return w_z

def ref_span(w_baf,mac,w_cr,w_bt): #mantido (precisa alterar na presente versão)
    '''
    Função que calcula a distância entre as cordas médias, envergadura de referência para uma asa mista reto-trapezoidal

    '''
    return w_baf+(mac/w_cr)*(w_bt-w_baf)

def lvt(ev_x, ev_cr, x_cg): #alterado (mas confirmar)
    '''
    Função que calcula a distância entre o EV e o CG em uma empenagem convencional
    
    Considera o centro aerodinâmico do perfil em 25% da corda
    '''
    # Entra a distância em y também
    return (ev_x + (ev_cr/4))-x_cg

def svt(ev_cr, ev_ct, ev_b): #alterado
    '''
    Função que calcula a área de um EV trapezoidal
    '''
    return (ev_cr+ev_ct)*ev_b/2

def vvt(lvt,svt,w_bt,s_ref): #mantido
    '''
    Função que calcula o volume de cauda vertical de uma empenagem em convencional com EV trapezoidal
    '''
    return ((lvt*svt)/(w_bt*s_ref))

def sht(eh_b,eh_cr, eh_ct): #alterado
    '''
    Função que calcula a área de um EH trapezoidal
    '''
    return eh_b*(eh_cr+eh_ct)/2

def lht(eh_x, eh_cr, x_cg): #alterado
    '''
    Função que calcula a distância entre o EH e o CG
    '''
    return (eh_x + (eh_cr/4))-x_cg

def vht(lht,sht,mac,s_ref): #mantido
    '''
    Função que calcula o volume de cauda horizontal de uma empenagem com EH retangular
    '''
    return (lht*sht)/(mac*s_ref)

def ar(b,s): #mantido
    '''
    Função que calcula a razão de aspecto de uma superfície utilizando a envergadura e área
    '''
    return (b**2)/s

def l_boom(fus_l, eh_x): #mantido 
    '''
    Função que calcula o comprimento do tailboom em função do comprimento da fuselagem, posição do eh e corda da raíz. Assumindo o início do boom na metade da fuselagem
    '''

    return eh_x-fus_l*0.5   # Boom começando no meio da fuselagem (possível ponto pra discussão)


class Prototype():

    '''
    Classe responsável por construir a geometria no formato do AVL a partir dos parâmetros de interesse
    w= referente à asa, eh= referente ao eh, ev= referente ao ev, b= envergadura, c= corda, r=raíz, t=ponta, af= afilamento, x e z = pontos do bordo de ataque.
    m= massa, x e z cg = localização do CG. 
    ge liga ou desliga o efeito solo.
    O número de painéis no AVL é ajustado diretamente no código desta classe.
    '''

    def __init__(self, w_bt, w_baf, w_cr, w_ci, w_ct, w_z, w_inc, w_wo, w_d, eh_b, eh_cr, eh_ct, eh_inc, eh_x, eh_z, ev_ct, ev_b, motor_x, motor_z= 0.30, ge= False):
        
        #w_ci, w_ct, eh_ct, ev_ct são frações (0 a 1) de outra quantidade. Para facilitar a restrição na otimização

        #Asa:   
        w_ci= w_ci*w_cr             # O input de w_ci é porcentagem da corda da raíz (w_cr), convertendo para [m]
        w_ct= w_ct*w_ci             # O input de w_ct é porcentagem da corda intermediária (w_ci), convertendo para [m]
        w_baf= w_baf*w_bt           # O input de w_baf é porcentagem do ponto de transição (w_bt), convertendo para [m]
        
        self.w_baf= w_baf           # Ponto de transição da envergadura
        self.w_bt= w_bt             # Envergadura total
        self.w_cr= w_cr             # Corda da raíz
        self.w_ci= w_ci             # Corda intermediária
        self.w_ct= w_ct             # Corda da ponta
        self.w_inc= w_inc           # Ângulo de incidência da asa
        self.w_wo= w_wo             # Washout na ponta da asa
        self.w_z= w_z               # Altura da asa em relação ao chão
        self.w_d= w_d               # Ângulo de diedro

        # EH
        eh_ct= eh_ct*eh_cr          # O input de eh_ct é porcentagem da corda da raíz (eh_cr), convertendo para [m]
        
        self.eh_b= eh_b             # Envergadura do EH
        self.eh_cr= eh_cr           # Corda da raíz do EH
        self.eh_ct= eh_ct           # Corda da ponta do EH
        self.eh_inc= eh_inc         # Ângulo de incidência do EH
        self.eh_x= eh_x             # Distância horizontal do bordo de atque do EH, em relação ao bordo de ataque da asa
        self.eh_z= eh_z             # Distância vertical do bordo de atque do EH, em relação ao solo

        # EV
        ev_cr= eh_cr                # Na configuração de empenagem convencional a corda do ev é igual à do eh
        ev_ct= ev_ct*ev_cr          # O input de ev_ct é porcentagem da corda da raíz (ev_cr), convertendo para [m]
        ev_x= eh_x                  # EV fixado com o EH
        ev_y= 0                     # Fixando ev_y no centro
        ev_z= eh_z                  # Ajuste da altura do EV, para ficar sobre o tailboom
        
        self.ev_b= ev_b             # Envergadura do EV
        self.ev_cr= ev_cr           # Corda da raíz EV
        self.ev_ct= ev_ct           # Corda da ponta EV
        self.ev_x= ev_x             # Distância horizontal do bordo de atque dos EV's, em relação ao bordo de ataque da asa
        self.ev_y= ev_y             # Distância no eixo Y dos EV's até o plano de simetria do avião
        self.ev_z= ev_z             # Distância vertical do bordo de atque dos EV's, em relação ao bordo de ataque da asa

        # MOTOR
        self.motor_x= motor_x       # Posição horizontal do motor. Vai ser negativa em uma configuração convencional
        self.motor_z= motor_z       # Posição vertical do motor
        self.pot= 600

        # FUSELAGEM E TAILBOOM
        fus_h= self.w_cr*0.12                      # Modelando as placas da fuselagem como retângulos de altura = 12% da corda da raíz
        fus_l= 1.25*self.w_cr
        fus_z= self.w_z - fus_h*0.5

        self.fus_z= fus_z                          # Posicionando o centro da fuselagem coincidente com a asa
        if fus_l < 0.5:                            # Definindo a fuselagem igual a 125% da corda da raiz da asa, mas não menor que 50 cm.
            self.fus_l = 0.5
        else:
            self.fus_l= fus_l
        self.fus_h= fus_h                          # Altura da fuselagem
        #self.x0_boom= self.fus_l-self.motor_x
        self.boom_l= l_boom(self.fus_l, self.eh_x)

        #VALORES DE REFERÊNCIA (ficar atento à implementação do cg aqui)
        self.s_ref= s_ref(self.w_cr, self.w_ci, self.w_baf, self.w_ct, self.w_bt)
        self.c_med= c_med(self.s_ref,self.w_bt)
        self.mac= mac(0, self.w_bt, self.w_baf, self.w_cr, self.w_ct)
        self.ref_span= ref_span(self.w_baf,self.mac,self.w_cr,self.w_bt)
        #Para o volume de cauda vertical
        self.svt= svt(self.ev_cr, self.ev_ct, self.ev_b)
        #Para o volume horizontal    
        self.sht= sht(self.eh_b,self.eh_cr, self.eh_ct)
        #Para a asa
        self.ar= ar(self.w_bt,self.s_ref)
        self.eh_ar= ar(self.eh_b,self.sht)

        # RESTRIÇÕES GEOMÉTRICAS
        self.eh_z_const= self.eh_z - self.w_z # Restrição geométrica para eh acima da asa
        
        #Dividindo as envergaduras pela metade devido à simetria. CUIDADO NA HORA DE CALCULAR A ÁREA E OUTRAS PROPRIEDADES MAIS TARDE!!!
        w_baf_h= self.w_baf/2
        w_bt_h= self.w_bt/2
        eh_b_h= self.eh_b/2
 
 ################################################### DEFINIÇÕES DE MASSA E ESTABILIDADE ###################################################
        # ESTABILIDADE
        self.pv= total_m(self.s_ref, self.sht, self.svt, self.fus_h, self.fus_l, self.boom_l)
        self.x_cg= cg(self.s_ref, self.w_z, self.w_cr, self.sht, self.eh_x, self.eh_z, self.eh_cr, self.svt, self.ev_x, self.ev_z, self.ev_cr, self.fus_z, self.fus_h, self.fus_l, self.boom_l, self.motor_x, self.motor_z)[0]
        self.z_cg= cg(self.s_ref, self.w_z, self.w_cr, self.sht, self.eh_x, self.eh_z, self.eh_cr, self.svt, self.ev_x, self.ev_z, self.ev_cr, self.fus_z, self.fus_h, self.fus_l, self.boom_l, self.motor_x, self.motor_z)[1]
        self.x_cg_p= self.x_cg/self.w_cr    # Posição do CG como fração da corda

        self.lvt= lvt(self.ev_x, self.ev_cr, self.x_cg)
        self.vvt= vvt(self.lvt,self.svt,self.w_bt,self.s_ref)

        self.lht= lht(self.eh_x, self.eh_cr, self.x_cg)
        self.vht= vht(self.lht,self.sht,self.mac,self.s_ref)

        self.low_cg= self.w_z - self.z_cg   # Restrição do CG abaixo da asa

################################################### DEFINIÇÃO DOS PERFIS ###################################################
        #Clmax dos perfis para detecção do estol
        e50s201550_clmax= 2.195 # Peril da raíz
        e30s201570_clmax= 2.243 # Perfil da ponta

        min1112_clmax= 2.42 # Peril da raíz
        min1209_clmax= 2.38 # Perfil da ponta
        
        #Definindo as polares para contabilização do arrasto parasita em cada perfil. Também vindo do xf

        e50s201550_profile_drag= ProfileDrag(cl=[-0.245,1.15,2.195],cd=[0.1896,0.015,0.0485])
        e30s201570_profile_drag= ProfileDrag(cl=[-0.26,1.15,2.243],cd=[0.192,0.015,0.048])

        min1112_profile_drag= ProfileDrag(cl=[0.4,1.65,2.42],cd=[0.085, 0.015, 0.0269])
        min1209_profile_drag= ProfileDrag(cl=[0.4, 1.25, 2.38],cd=[0.06, 0.0177, 0.043])

        naca0012_profile_drag= ProfileDrag(cl=[-1.128,0.0,1.128],cd=[0.038,0.0077,0.038])
        naca4412_s1223_70_profile_drag= ProfileDrag(cl=[-1.67,-0.57,0.068],cd=[0.0247,0.01,0.042])

        # O arquivo .dat deve estar junto com o arquivo deste código, colocar os perfis em uma pasta separada, em primeira análise, gera erros
        root_foil='MIN1112.dat'
        tip_foil='MIN1209.dat'
        eh_foil='NACA4412_S1223_70.dat'

        root_profile_drag= min1112_profile_drag
        tip_profile_drag= min1209_profile_drag
        eh_profile_drag= naca4412_s1223_70_profile_drag

        self.w_root_clmax= min1112_clmax
        self.w_tip_clmax= min1209_clmax
        
################################################### Definindo as secções de cada superfície ###################################################
        self.w_root_section = Section(leading_edge_point=Point(0, 0, w_z),
                                    chord=w_cr,
                                    airfoil=FileAirfoil(root_foil),
                                    profile_drag= root_profile_drag
                                    )
        
        self.w_trans_section = Section(leading_edge_point=Point((w_cr-w_ci)/4, w_baf_h, w_z + z_d(w_baf_h,w_d)),
                                    chord=w_ci,
                                    airfoil=FileAirfoil(root_foil),
                                    profile_drag= root_profile_drag
                                    )
        
        self.w_tip_section = Section(leading_edge_point=Point(((w_cr-w_ci)/4) + ((w_ci-w_ct)/4) , w_bt_h, w_z + z_d(w_bt_h,w_d)), #necessário incluir função para transformar o ângulo do diedro em altura do perfil
                                    chord=w_ct,
                                    airfoil=FileAirfoil(tip_foil),
                                    profile_drag= tip_profile_drag,
                                    angle= self.w_wo
                                    )
        
        self.elevator = Control(name="elevator",
                                gain=1.0,
                                x_hinge=0.4,
                                duplicate_sign=1.0)

        self.eh_root_section = Section(leading_edge_point=Point(eh_x, 0, eh_z),
                                        chord=eh_cr,
                                        airfoil=FileAirfoil(eh_foil),
                                        profile_drag= eh_profile_drag,
                                        controls= [self.elevator]
                                        )
        
        self.eh_tip_section = Section(leading_edge_point=Point(eh_x + (eh_cr-eh_ct)/4, eh_b_h, eh_z),
                                        chord=eh_ct,
                                        airfoil=FileAirfoil(eh_foil),
                                        profile_drag= eh_profile_drag,
                                        controls= [self.elevator]
                                        )
        
        self.ev_root_section = Section(leading_edge_point=Point(ev_x, 0, ev_z),
                                        chord=ev_cr,
                                        airfoil=NacaAirfoil(naca='0012'),
                                        profile_drag= naca0012_profile_drag
                                        )
        
        self.ev_tip_section = Section(leading_edge_point=Point(ev_x + (ev_cr-eh_ct)/4, 0, ev_z+ev_b),
                                        chord=ev_ct,
                                        airfoil=NacaAirfoil(naca='0012'),
                                        profile_drag= naca0012_profile_drag
                                        )
        
######################################################## Definindo as superfícies com base nas secções ########################################################
        self.wing_surface = Surface(name="Wing",
                                    n_chordwise=12,
                                    chord_spacing=Spacing.cosine,
                                    n_spanwise=22,
                                    span_spacing=Spacing.neg_sine,
                                    #y_duplicate=0.0,
                                    sections=[self.w_root_section,self.w_trans_section, self.w_tip_section],
                                    angle= self.w_inc
                                    )
        
        self.eh_surface = Surface(name="Horizontal_Stabilizer",
                                    n_chordwise=8,
                                    chord_spacing=Spacing.cosine,
                                    n_spanwise=10,
                                    span_spacing=Spacing.equal,
                                    #y_duplicate=0.0,
                                    sections=[self.eh_root_section, self.eh_tip_section],
                                    angle= self.eh_inc
                                    )
        
        self.ev_surface = Surface(name="Vertical_Stabilizer",
                                    n_chordwise=8,
                                    chord_spacing=Spacing.cosine,
                                    n_spanwise=8,
                                    span_spacing=Spacing.equal,
                                    #y_duplicate=0.0,
                                    sections=[self.ev_root_section, self.ev_tip_section]
                                    )

############################################# Definição da geometria com e sem o efeito solo (método das imagens) #############################################
        if ge:
            #Todas as dimensões de referência são calculadas diretamente, mas podem ser implementadas funções mais acima
            self.geometry = Geometry(name="Prototype",
                                    reference_area= self.s_ref/2,
                                    reference_chord= self.mac,
                                    reference_span= self.ref_span/2,
                                    reference_point=Point(self.x_cg, 0, self.z_cg),
                                    surfaces=[self.wing_surface, self.eh_surface, self.ev_surface],
                                    y_symmetry=Symmetry.symmetric,
                                    z_symmetry=Symmetry.symmetric,
                                    z_symmetry_plane= 0.00
                                    )

        else:

            self.geometry = Geometry(name="Prototype",
                                    reference_area= self.s_ref/2,
                                    reference_chord= self.mac,
                                    reference_span= self.ref_span/2,
                                    reference_point= Point(self.x_cg, 0, self.z_cg),
                                    surfaces=[self.wing_surface, self.eh_surface, self.ev_surface],
                                    y_symmetry=Symmetry.symmetric
                                    )

        

    #Método utilizado para mostrar em interface gráfica a geometria do protótipo
    def show_geometry(self):

        geometry_session= Session(geometry= self.geometry, cases=[])
        geometry_session.show_geometry()

    #if __name__ == '__main__':

        #print(s_ref(0.566,0.421152*2,0.172,1.09675*2))
        

if __name__ == '__main__':
        banana = Prototype(3.5, 0.5, 0.5, 1, 0.8, 0.2, 2, 0, 0, 1, 0.25, 1, 0, 1.2, 0.4, 1, 0.4, -0.2, motor_z= 0.30, ge= False)
        banana.show_geometry()
        print(banana.ar, banana.eh_ar)