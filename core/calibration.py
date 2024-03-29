"""Calibration module."""
import numpy as np

from typing import Dict 

import os
import json
from core.config import ROOTDIR
from core.transform import (
    BaseToCCRadar,
    BaseToSCRadar,
    BaseToLidar,
    BaseToImu,
    BaseToVicon,
)


class AntennaConfig:
    """Antenna configuration.

    Attributes:
        num_rx (int): Number of reception antenna
        num_tx (int): Number of transmission antenna
        f_design (float): Base frequency the sensor has been designed for
        rxl (NDArray): Array describing the configuration of the
            reception antenna in unit of half-wavelengths
        txl (NDArray): Array describing the configuration of the
            transmission antenna in unit of half-wavelengths

    NOTE:
        The 'rxl' and 'txl' arrays describe the antenna layout using the
        followinf structure [idx az, el].

        Thus, the first column indicates the index number of the array.
        The second is the azimuth position of each antenna in half a wave
        length and the last column their elevation position.

        It's important to keep in mind that the row wise ordering of those
        matrices is [dev4, dev1, dev3, dev2] for the cascade radar.
    """

    def __init__(self, filepath: str) -> None:
        """Init Antenna config.

        Argument:
            filepath: Path to the antenna configuration file
        """
        rxl = []    # RX layout
        txl = []    # TX layout
        with open(os.path.join(ROOTDIR, filepath), "r") as fh:
            for line in fh:
                if line.startswith("# "):
                    continue
                else:
                    chunks = line.strip().split(" ")
                    if chunks[0] == "rx":
                        rxl.append([int(x) for x in chunks[1:]])
                    elif chunks[0] == "tx":
                        txl.append([int(x) for x in chunks[1:]])
                    else:
                        setattr(self, chunks[0].lower(), float(chunks[1]))
        self.num_rx = int(self.num_rx)
        self.num_tx = int(self.num_tx)
        self.rxl = np.array(rxl)
        self.txl = np.array(txl)


class CouplingCalibration:
    """Coupling calibration.

    Attributes:
        num_rx (int): Number of reception antenna
        num_tx (int): Number of transmission antenna
        num_range_bins (int): Number of range bins
        num_doppler_bins (int): Number of doppler frequency bins
        data (list[float]): Array description coupling calibartion data

    TODO: Process rge raw calibration data
    """

    def __init__(self, filepath: str) -> None:
        """Init coupling calibration."""
        with open(os.path.join(ROOTDIR, filepath), "r") as fh:
            for line in fh:
                if line.startswith("# "):
                    continue
                else:
                    name, value = line.split(":")
                    value = value.split(",")
                    if len(value) > 1:
                        setattr(self, name.lower(), [float(x) for x in value])
                    else:
                        setattr(self, name.lower(), int(value[0]))


class HeatmapConfiguration:
    """Heatmap configuration.

    Attributes:
        num_range_bins (int): Number of range bins
        num_elevation_bins (int): Number of elevation bins
        num_azimuth_bins (int): Number of azimuth bins
        range_bin_width (float): Width of range bin - range resolution
        azimuth_bins (list[float]): Array describing the azimuth bin
        elevation_bins (list[float]): Array describing the elevation bin
    """

    def __init__(self, filepath: str) -> None:
        """Init heatmap configuration."""
        with open(os.path.join(ROOTDIR, filepath), "r") as fh:
            for line in fh:
                if line.startswith("# "):
                    continue
                else:
                    value: list[str] = line.split(" ")
                    if len(value) > 2:
                        setattr(self, value[0].lower(), [float(x) for x in value[1:-1]])
                    else:
                        setattr(self, value[0].lower(), float(value[1]))
        self.num_range_bins = int(self.num_range_bins)
        self.num_elevation_bins = int(self.num_elevation_bins)
        self.num_azimuth_bins = int(self.num_azimuth_bins)


class WaveformConfiguration:
    """Waveform configuration.

    Attributes:
        num_rx (int): Number of reception antenna
        num_tx (int): Number of transmission antenna
        num_adc_samples_per_chirp (int): Number of ADC samples per chirp
        num_chirps_per_frame (int):  Number of chirp per frame
        adc_sample_frequency (float): ADC sampling frequency in herz
        start_frequency (float): Chirp start frequency in herz
        idle_time (float): Idle time before starting a new chirp in second
        adc_start_time (float): Start time of ADC in second
        ramp_end_time (float): End time of frequency ramp
        frequency_slope (float): Frequency slope
    """

    def __init__(self, filepath: str) -> None:
        """Init waveform configuration."""
        with open(os.path.join(ROOTDIR, filepath), "r") as fh:
            for line in fh:
                if line.startswith("# "):
                    continue
                else:
                    name, value = line.split(" ")
                    setattr(self, name.lower(), float(value))
        self.num_rx = int(self.num_rx)
        self.num_tx = int(self.num_tx)
        self.num_adc_samples_per_chirp = int(self.num_adc_samples_per_chirp)
        self.num_chirps_per_frame = int(self.num_chirps_per_frame)


class PhaseCalibration:
    """Phase/Frequency calibration.

    Attributes:
        num_rx (int): Number of reception antenna
        num_tx (int): Number of transmission antenna
        frequency_slope (float): Frequency slope
        sampling_rate (float): ADC sampling frequency in Herz
        frequency_calibration_matrix (list[float]): Sensor frequency
        calibration matrix
    """

    def __init__(self, filepath: str) -> None:
        """Init Phase/Frequency configuration."""
        with open(os.path.join(ROOTDIR, filepath), "r") as fh:
            config = json.load(fh)
            setattr(self, "num_rx", config["antennaCalib"]["numRx"])
            setattr(self, "num_tx", config["antennaCalib"]["numTx"])
            setattr(self,
                "frequency_slope",
                config["antennaCalib"]["frequencySlope"]
            )
            setattr(self,
                "sampling_rate",
                config["antennaCalib"]["samplingRate"]
            )
            setattr(self,
                "frequency_calibration_matrix",
                config["antennaCalib"]["frequencyCalibrationMatrix"]
            )
            setattr(self,
                "phase_calibration_matrix",
                config["antennaCalib"]["phaseCalibrationMatrix"]
            )


class SCRadarCalibration:
    """Single Chip Radar Calibration.

    Holds the single chip radar sensor calibration parameters

    Attributes:
        antenna: Antenna configuration
        coupling: Antenna coupling calibration
        heatmap: Heatmap recording configuration
        waveform: Waveform generation parameters and calibration
        d: The optimal inter-antenna distance estimation in unit of
           a wavelength
    """

    def __init__(self, config: Dict[str, str]=[]) -> None:
        """Init Single Chip radar calibration.

        Arguemnt:
            config: Dictionary containing the paths to files holding the
            radar calibration settiings. The main keys are:

                "antenna": Antenna calibration
                "couling": Coupling calibration
                "heatmap": heatmap configuration
                "waveform": Waveform configuration

            NOTE: See dataset.json
        """
                
        self.antenna = AntennaConfig(config["antenna"])
        self.coupling = CouplingCalibration(config["coupling"])
        self.waveform = WaveformConfiguration(config["waveform"])
        self.heatmap = HeatmapConfiguration(config["heatmap"])

        # Chirp start frequency in GHz
        fstart: float = self.waveform.start_frequency / 1e9
        # Chirp slope in GHz/s
        fslope: float = self.waveform.frequency_slope / 1e9
        # ADC sampling frequency in Hz
        fsample: float = self.waveform.adc_sample_frequency
        # Chrip sampling time in s
        stime: float = self.waveform.num_adc_samples_per_chirp / fsample
        # Antenna PCB design base frequency
        fdesign: float = self.antenna.f_design
        self.d = 0.5 * ((fstart + (fslope * stime) / 2) / fdesign)

    def get_coupling_calibration(self) -> np.array:
        """Return the coupling calibration array to apply on the range fft."""
        return np.array(self.coupling.data).reshape(
            self.coupling.num_tx,
            self.coupling.num_rx,
            1,
            self.waveform.num_adc_samples_per_chirp,
        )

# Reference： file/signalPrcesssing_userguide_4chipCascade.pdf
class CCRadarCalibration(SCRadarCalibration):
    """Cascade Chip Radar Calibration.

    Holds the cascade chip radar sensor calibration parameters

    Attributes:
        antenna: Antenna configuration
        coupling: Antenna coupling calibration
        heatmap: Heatmap recording configuration
        waveform: Waveform generation parameters and calibration
        phase: Phase and frequency calibration
    """

    def __init__(self, config: Dict[str, str]) -> None:
        """Init Cascade Chip Radar calibration.

        Argument:
            config: In addition to the keys present in the super class,
            this config add the following one

                "phase": Phase and frequency calibration

        NOTE: See dataset.json
        """
        super(CCRadarCalibration, self).__init__(config)
        self.phase = PhaseCalibration(config["phase"])

    # 4.2 Apply calibration matrix in MIMO operation ——> Second Step: phase and amplitude calibration
    def get_phase_calibration(self) -> np.array:
        """Return the phase calibration array."""
        # Phase calibrationm atrix
        pm = np.array(self.phase.phase_calibration_matrix)
        pm = pm[::2] + 1j * pm[1::2]
        pm = pm[0] / pm
        return pm.reshape(
            self.phase.num_tx,
            self.phase.num_rx,
            1,
            1
        )

    # 4.2 Apply calibration matrix in MIMO operation ——> First step: frequency calibration
    def get_frequency_calibration(self) -> np.array:
        """Return the frequency calibration array."""
        num_tx: int = self.phase.num_tx
        num_rx: int = self.phase.num_rx

        # Calibration frequency slope
        fcal_slope: float = self.phase.frequency_slope
        # Calibration sampling rate
        cal_srate: int = self.phase.sampling_rate

        fcal_matrix = np.array(self.phase.frequency_calibration_matrix)

        fslope: float = self.waveform.frequency_slope
        srate: int = self.waveform.adc_sample_frequency

        # Delta P
        # 
        dp = fcal_matrix - fcal_matrix[0]

        cal_matrix = 2 * np.pi * dp * (fslope / fcal_slope) * (cal_srate / srate)
        cal_matrix /= self.waveform.num_adc_samples_per_chirp
        cal_matrix.reshape(num_tx, num_rx)
        cal_matrix = np.expand_dims(cal_matrix, -1) * np.arange(
            self.waveform.num_adc_samples_per_chirp
        )
        return np.exp(-1j * cal_matrix).reshape(
            num_tx,
            num_rx,
            1,
            self.waveform.num_adc_samples_per_chirp
        )


class BaseTransform:
    """Base transforms.

    Tranform to rotate and/or translate a point from the base coordinate frame
    to sensor specific coordinate frame.

    Attributes:
        to_ccradar: Tranfrom from base to cascade chip radar sensor coordinate
        frame
        to_scradar: Tranfrom from base to single chip radar sensor coordinate
        frame
        to_imu: Tranfrom from base to IMU sensor coordinate frame
        to_lidar: Tranfrom from base to lidar sensor coordinate frame
        to_vicon: Tranfrom from base to vicon sensor coordinate frame
    """

    def __init__(self, config: Dict[str, str]=[]) -> None:
        """Init base transforms.

        Argument:
            config: Dictionary decribing the path to the transform files

        NOTE: See dataset.json
        """
        self.to_ccradar = BaseToCCRadar(config["base-to-ccradar"])
        self.to_scradar = BaseToSCRadar(config["base-to-scradar"])
        self.to_imu = BaseToImu(config["base-to-imu"])
        self.to_lidar = BaseToLidar(config["base-to-lidar"])
        self.to_vicon = BaseToVicon(config["base-to-lidar"])


class Calibration:
  """Calibration."""

  def __init__(self, rootdir: Dict[str, Dict[str, str]]=[]) -> None:
      """Init.

      Argument:
        rootdir: Root directories to access sensors calibration config
      """
      self.scradar = SCRadarCalibration(rootdir["scradar"])
      self.ccradar = CCRadarCalibration(rootdir["ccradar"])
      self.transform = BaseTransform(rootdir["transform"])
