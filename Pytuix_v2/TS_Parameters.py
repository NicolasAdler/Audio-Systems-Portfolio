import math

class TS_Parameters:
    PI = math.pi
    RHO = 1.225   # Air density (kg/m^3)
    C = 343       # Speed of sound (m/s)

    def __init__(self):
        # User-facing values (stored in UI units: liters, Hz, mm, cm^2, Ohms, mm/N, grams, Watts)
        self.Vas = 0.0
        self.fs = 0.0
        self.Qts = 0.0
        self.Qes = 0.0
        self.Qms = 0.0
        self.Xmax = 0.0
        self.Sd = 0.0
        self.Sensitivity = 0.0
        self.Mms = 0.0
        self.Cms = 0.0
        self.Kms = 0.0
        self.Rms = 0.0
        self.n0 = 0.0
        self.Re = 0.0
        self.Res = 0.0
        self.Bl = 0.0
        self.Vb = 0.0
        self.W = 0.0

        # State tracking indicators
        self.user_inputs = {}

    def set_Mms(self, Mms=None, fs=None, Cms=None):
        if Mms is not None:
            self.Mms = Mms
        elif fs is not None and Cms is not None:
            # Cms is in mm/N -> convert to m/N (* 1e-3)
            # Resulting Mms is in kg -> convert to grams (* 1000)
            cms_m_n = Cms * 1e-3
            if cms_m_n > 0 and fs > 0:
                mms_kg = 1.0 / (math.pow(2 * self.PI * fs, 2) * cms_m_n)
                self.Mms = mms_kg * 1000
            else:
                self.Mms = 0.0

    def set_Cms(self, Cms):
        self.Cms = Cms

    def set_Cms_with_Mms_and_fs(self, fs, Mms):
        # Mms is in grams -> convert to kg (/ 1000)
        # Resulting Cms is in m/N -> convert to mm/N (* 1000)
        mms_kg = Mms / 1000.0
        if fs > 0 and mms_kg > 0:
            cms_m_n = 1.0 / (4.0 * (self.PI ** 2) * (fs ** 2) * mms_kg)
            self.Cms = cms_m_n * 1000.0
        else:
            self.Cms = 0.0

    def set_Vas(self, Vas=None, Sd=None, Cms=None):
        if Vas is not None:
            self.Vas = Vas
        elif Sd is not None and Cms is not None:
            # Sd is in cm^2 -> convert to m^2 (/ 10000)
            # Cms is in mm/N -> convert to m/N (/ 1000)
            # Resulting Vas is in m^3 -> convert to Liters (* 1000)
            sd_m2 = Sd / 10000.0
            cms_m_n = Cms / 1000.0
            vas_m3 = self.RHO * (self.C ** 2) * (sd_m2 ** 2) * cms_m_n
            self.Vas = vas_m3 * 1000.0

    def set_Kms(self, Kms):
        self.Kms = Kms

    def set_Kms_with_Cms(self, Cms):
        # Cms is in mm/N. Kms is in N/mm.
        self.Kms = 1.0 / Cms if Cms != 0.0 else 0.0

    def set_fs(self, fs=None, Cms=None, Mms=None):
        if fs is not None:
            self.fs = fs
        elif Cms is not None and Mms is not None:
            cms_m_n = Cms / 1000.0
            mms_kg = Mms / 1000.0
            if cms_m_n > 0 and mms_kg > 0:
                self.fs = (1.0 / (2.0 * self.PI)) * math.sqrt(1.0 / (cms_m_n * mms_kg))
            else:
                self.fs = 0.0

    def set_Qts(self, Qts=None, Qes=None, Qms=None):
        if Qts is not None:
            self.Qts = Qts
        elif Qes is not None and Qms is not None:
            if (Qms + Qes) != 0:
                self.Qts = (Qms * Qes) / (Qms + Qes)
            else:
                self.Qts = 0.0

    def set_Sd(self, Sd):
        self.Sd = Sd

    def set_Xmax(self, Xmax=None, cone_height=None, gap_height=None):
        if Xmax is not None:
            self.Xmax = Xmax
        elif cone_height is not None and gap_height is not None:
            self.Xmax = abs((cone_height - gap_height) / 2.0)

    def set_Rms(self, Rms=None, fs=None, Mms=None, Qms=None):
        if Rms is not None:
            self.Rms = Rms
        elif fs is not None and Mms is not None and Qms is not None:
            # Mms in grams -> convert to kg (/ 1000)
            mms_kg = Mms / 1000.0
            if Qms > 0 and fs > 0:
                self.Rms = (2.0 * self.PI * fs * mms_kg) / Qms
            else:
                self.Rms = 0.0

    def set_n0(self, n0=None, fs=None, Vas=None, Qes=None):
        if n0 is not None:
            self.n0 = n0
        elif fs is not None and Vas is not None and Qes is not None:
            # Vas is in liters -> convert to m^3 (/ 1000)
            vas_m3 = Vas / 1000.0
            if Qes > 0:
                # Standard reference formula using custom acoustic constants
                self.n0 = (4 * (self.PI ** 2) / (self.C ** 3)) * (fs ** 3) * (vas_m3 / Qes)
            else:
                self.n0 = 0.0

    def set_Sensitivity(self, Sensitivity):
        self.Sensitivity = Sensitivity

    def set_Sensitivity_with_n0(self, n0):
        if n0 > 0:
            self.Sensitivity = 112.2 + 10 * math.log10(n0)

    def set_Qes(self, Qes=None, Qms=None, Re=None, Res=None, Qts=None):
        if Qes is not None:
            self.Qes = Qes
        elif Qms is not None and Re is not None and Res is not None:
            if Res != 0:
                self.Qes = Qms * (Re / Res)
            else:
                self.Qes = 0.0
        elif Qts is not None and Qms is not None:
            self.Qes = (Qms * Qts) / (Qms - Qts) if (Qms - Qts) != 0 else 0.0

    def set_Qms(self, Qms=None, Qes=None, Re=None, Res=None, Qts=None):
        if Qms is not None:
            self.Qms = Qms
        elif Qes is not None and Re is not None and Res is not None:
            if Re != 0:
                self.Qms = Qes * (Res / Re)
            else:
                self.Qms = 0.0
        elif Qts is not None and Qes is not None:
            self.Qms = (Qes * Qts) / (Qes - Qts) if (Qes - Qts) != 0 else 0.0

    def set_Re(self, Re): self.Re = Re
    def set_Bl(self, Bl): self.Bl = Bl
    def set_Vb(self, Vb): self.Vb = Vb
    def set_W(self, W): self.W = W

    def solve(self):
        while True:
            update = False
            if self.Vas == 0.0 and self.Sd != 0.0 and self.Cms != 0.0:
                self.set_Vas(Sd=self.Sd, Cms=self.Cms)
                update = True
            if self.Cms == 0.0 and self.fs != 0.0 and self.Mms != 0.0:
                self.set_Cms_with_Mms_and_fs(self.fs, self.Mms)
                update = True
            if self.Mms == 0.0 and self.fs != 0.0 and self.Cms != 0.0:
                self.set_Mms(fs=self.fs, Cms=self.Cms)
                update = True
            if self.Kms == 0.0 and self.Cms != 0.0:
                self.set_Kms_with_Cms(self.Cms)
                update = True 
            if self.fs == 0.0 and self.Cms != 0.0 and self.Mms != 0.0:
                self.set_fs(Cms=self.Cms, Mms=self.Mms)
                update = True
            if self.Qts == 0.0 and self.Qes != 0.0 and self.Qms != 0.0:
                self.set_Qts(Qes=self.Qes, Qms=self.Qms)
                update = True
            if self.Qms == 0.0 and self.Qts != 0.0 and self.Qes != 0.0:
                self.set_Qms(Qts=self.Qts, Qes=self.Qes)
                update = True
            if self.Qes == 0.0 and self.Qts != 0.0 and self.Qms != 0.0:
                self.set_Qes(Qts=self.Qts, Qms=self.Qms)
                update = True
            if self.Rms == 0.0 and self.fs != 0.0 and self.Mms != 0.0 and self.Qms != 0.0:
                self.set_Rms(fs=self.fs, Mms=self.Mms, Qms=self.Qms)
                update = True
            if self.n0 == 0.0 and self.fs != 0.0 and self.Vas != 0.0 and self.Qes != 0.0:
                self.set_n0(fs=self.fs, Vas=self.Vas, Qes=self.Qes)
                update = True
            if self.Sensitivity == 0.0 and self.n0 != 0.0:
                self.set_Sensitivity_with_n0(self.n0)
                update = True
            if not update:
                break
