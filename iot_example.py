import paho.mqtt.client as mqtt # Εισαγωγή βιβλιοθηκών
import matplotlib.pyplot as plt
import ssl
import os
import sys
from matplotlib.widgets import Button #Εισαγωση κουμπί
from threading import Timer
from datetime import datetime

class IoTExample:
    def __init__(self): #Main συνάρτηση
        self.ax = None
        self._prepare_graph_window()
        #Δημιουργούμε ένα αντικείμενο ώστε η μεταβλητή να είναι διαθέσιμη και στις υπόλοιπες μεθόδους της κλάσης μας 
        self.client = mqtt.Client()  
        #Με αυτή την εντολή ορίζουμε ότι μόλις ολοκληρωθεί η εγκατάσταση της σύνδεσης, θα κληθεί η μέθοδος _on_connect(self, client, userdata, flags, rc) της τρέχουσας κλάσης
        self.client.on_connect = self._on_connect 
        #Με αυτή την εντολή ορίζουμε ότι ησυνάρτηση _on_log(self, client, userdata, level, buf) θα χρησιμοποιείται για την παραγωγή διαγνωστικών μηνυμάτων σχετικάμε τη σύνδεση με το MQTT
        self.client.on_log = self._on_log 
        #Με αυτή την εντολή ορίζουμε ότι κάθε φορά που θα λαμβάνεται ένα μήνυμα θα καλείται η συνάρτηση _on_message(self, client, userdata, msg)
        self.client.on_message = self._on_message #
        #Για να συνδεθει με τον broker
        self._establish_mqtt_connection()
        
        #Καλώ αυτήν την μέθοδο για να ξεκινήσω client loop
    def start(self):
        if self.ax:
            self.client.loop_start()
            plt.show()
        else:
            #Με αυτή την μέθοδο μπλοκάρουμε την εκτέλεση του προγράμματος ώστε να μην τερματίσει και να αναμένει για μηνύματα
            self.client.loop_forever()
    #Καλώ αυτήν την μέθοδο για να αποσυνδεθώ broker
    def disconnect(self, args=None):
        #αποσύνδεση
        self.client.disconnect()

    #Για να συνδεθώ στον broker
    def _establish_mqtt_connection(self):
        #Με αυτή τη μέθοδο ορίζουμε ότι θα χρησιμοποιήσουμε κρυπτογράφηση για τη μετάδοση/λήψη των μηνυμάτων
        self.client.tls_set_context(ssl.SSLContext(ssl.PROTOCOL_TLSv1_2))
        #Με αυτή τη μέθοδο ορίζουμε το όνομα χρήστη με το password
        self.client.username_pw_set('iotlesson', 'YGK0tx5pbtkK2WkCBvJlJWCg')
        # Με αυτή τη μέθοδο ξεκινάμε τη σύνδεση με τον MQTT broker, και ορίζουμε το DNS όνομα του διακομιστή, και την πόρτα που θα γίνει η σύνδεση
        self.client.connect('phoenix.medialab.ntua.gr', 8883)

    #Αυτήν η συνάρτηση θα καλεστεί αφού πραγματοποιηθεί η σύνδεση
    def _on_connect(self, client, userdata, flags, rc):
        #Αυτή η μέθοδος καλείται αφού έχει πραγματοποιηθεί η σύνδεση, ώστε να αρχίσει να παρακολουθεί το topic που είναι στην παράμετρο
        client.subscribe('hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state') 

    #αρχικοποίηση του γραφήματος
    def _prepare_graph_window(self):
        #τιμές παραθύρου
        plt.rcParams['toolbar'] = 'None' 
        self.ax = plt.subplot(111)
        self.dataX = []
        self.dataY = []
        self.first_ts = datetime.now()
        self.lineplot, = self.ax.plot(
        self.dataX, self.dataY, linestyle='--', marker='o', color='b')
        self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)
        self.finishing = False
        #προσθέτουμε 2 κουμπιά και ένα πεδίο κειμένου στο γράφημα
        axcut = plt.axes([0.0, 0.0, 0.1, 0.06])
        self.bcut = Button(axcut, 'ON')
        axcut2 = plt.axes([0.1, 0.0, 0.1, 0.06])
        self.bcut2 = Button(axcut2, 'OFF')
        self.state_field = plt.text(1.5, 0.3, 'STATE: -')
        self.bcut.on_clicked(self._button_on_clicked)
        self.bcut2.on_clicked(self._button_off_clicked)
        self._my_timer()

    #Για την ανανέωση του γραφήματος όταν λαμβάνονται νέα αποτελέσματα ή αλλάζει η απεικόνιση του άξονα x
    def _refresh_plot(self):
        if len(self.dataX) > 0:
            self.ax.set_xlim(min(self.first_ts, min(self.dataX)),max(max(self.dataX), datetime.now()))
            self.ax.set_ylim(min(self.dataY) * 0.8, max(self.dataY) * 1.2)
            self.ax.relim()
        else:
            self.ax.set_xlim(self.first_ts, datetime.now())
            self.ax.relim()
        plt.draw()

    #Για να προσθέτουμε μια νέα τιμή στο γράφημα:
    def _add_value_to_plot(self, value):
        self.dataX.append(datetime.now())
        self.dataY.append(value)
        self.lineplot.set_data(self.dataX, self.dataY)
        self._refresh_plot()

    #Για την αυτόματη μετακίνηση του γραφήματος δεξιά κάθε δευτερόλεπτο
    def _my_timer(self):
        self._refresh_plot()
        if not self.finishing:
            Timer(1.0, self._my_timer).start()

    #καλείται όταν πατήσω το κουμπί On
    def _button_on_clicked(self, event): #Συνάρτηση listener on click
        #Αυτή η μέθοδος χρησιμοποιείται για την αποστολή μηνύματος προς τον MQTT broker. On για την ενεργοποίηση του φορτίού
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'ON') 
    #καλείται όταν πατήσω το κουμπί Off
    def _button_off_clicked(self, event):  #Συνάρτηση listener on click
        #off για την απενεργοποίηση του φορτίου
        self.client.publish('hscnl/hscnl02/sendcommand/ZWaveNode005_Switch', 'OFF')  

    #Καλείται όποτε έρχεται ένα νέο μυνημα ληφθεί
    def _on_message(self, client, userdata, msg): 
        #Μόλις λαβει νέο μήνυμα τοποθετεί την τιμή στο σχεδιάγραμμα
        if msg.topic == 'hscnl/hscnl02/state/ZWaveNode005_ElectricMeterWatts/state':self._add_value_to_plot(float(msg.payload))
        print(msg.topic+' '+str(msg.payload))
    #Καλείται όποτε έχουμε μια νέα καταγραφή και μας εμφανιζει τις καταγραφες στο terminal
    def _on_log(self, client, userdata, level, buf):
        print('log: ', buf)


try:
    iot_example = IoTExample()
    iot_example.start()
except KeyboardInterrupt:
    print("Interrupted")
    try:
        iot_example.disconnect()
        sys.exit(0)
    except SystemExit:
        os._exit(0)