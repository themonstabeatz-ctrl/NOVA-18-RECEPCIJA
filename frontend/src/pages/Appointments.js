import React, { useState, useEffect } from 'react';
import { appointmentService, therapistService, serviceService, businessHoursService } from '../services/api';
import { Plus, Edit2, Trash2, X, Calendar as CalendarIcon, Check, ChevronLeft, ChevronRight, Printer } from 'lucide-react';
import BodyMap from '../components/BodyMap';

const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [therapists, setTherapists] = useState([]);
  const [services, setServices] = useState([]);
  const [businessHours, setBusinessHours] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [appointmentToPrint, setAppointmentToPrint] = useState(null);
  const [formData, setFormData] = useState({
    client_first_name: '',
    client_last_name: '',
    client_phone: '',
    client_email: '',
    therapist_id: '',
    service_id: '',
    start_time: '',
    status: 'scheduled',
    body_map_gender: '',
    body_map_points: [],
  });

  // Translations for print
  const translations = {
    sr: {
      title: 'LIST ZA MASAŽU',
      client: 'Klijent:',
      appointmentDate: 'Datum termina:',
      time: 'Vreme:',
      service: 'Usluga:',
      therapist: 'Terapeut:',
      bodyMap: 'Mapa tela - Označene oblasti za masažu',
      frontSide: 'Prednja strana',
      backSide: 'Zadnja strana',
      markedPoints: 'označenih tačaka'
    },
    th: {
      title: 'รายการนวด',
      client: 'ลูกค้า:',
      appointmentDate: 'วันที่นัดหมาย:',
      time: 'เวลา:',
      service: 'บริการ:',
      therapist: 'นักบำบัด:',
      bodyMap: 'แผนที่ร่างกาย - พื้นที่ที่ทำการนวด',
      frontSide: 'ด้านหน้า',
      backSide: 'ด้านหลัง',
      markedPoints: 'จุดที่ทำเครื่องหมาย'
    }
  };

  // Helper functions for date format conversion
  const formatDateToDDMMYYYY = (dateString) => {
    // Convert YYYY-MM-DD to DD/MM/YYYY
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const formatDateToYYYYMMDD = (ddmmyyyyString) => {
    // Convert DD/MM/YYYY to YYYY-MM-DD
    const parts = ddmmyyyyString.split('/');
    if (parts.length === 3) {
      return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }
    return ddmmyyyyString;
  };

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const startOfDay = `${selectedDate}T00:00:00`;
      const endOfDay = `${selectedDate}T23:59:59`;

      const [appointmentsRes, therapistsRes, servicesRes, hoursRes] = await Promise.all([
        appointmentService.getAll({ start_date: startOfDay, end_date: endOfDay }),
        therapistService.getAll(true),
        serviceService.getAll(),
        businessHoursService.get(),
      ]);

      setAppointments(appointmentsRes.data);
      setTherapists(therapistsRes.data);
      setServices(servicesRes.data);
      setBusinessHours(hoursRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // datetime-local gives us "2025-10-19T14:00" format
      // We need to send it as-is with just :00 for seconds
      const dateTimeString = formData.start_time.includes('T') 
        ? `${formData.start_time}:00` 
        : formData.start_time;
      
      const data = {
        ...formData,
        start_time: dateTimeString,
      };

      if (editingAppointment) {
        await appointmentService.update(editingAppointment.id, data);
      } else {
        await appointmentService.create(data);
      }
      fetchData();
      handleCloseModal();
    } catch (error) {
      console.error('Error saving appointment:', error);
      const errorMsg = error.response?.data?.detail || 'Greška pri čuvanju termina';
      alert(errorMsg);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Da li ste sigurni da želite da obrišete ovaj termin?')) {
      try {
        await appointmentService.delete(id);
        fetchData();
      } catch (error) {
        console.error('Error deleting appointment:', error);
        alert('Greška pri brisanju termina');
      }
    }
  };

  const handleEdit = (appointment) => {
    setEditingAppointment(appointment);
    const startTime = new Date(appointment.start_time);
    const localDateTime = new Date(startTime.getTime() - startTime.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);

    setFormData({
      client_first_name: appointment.client_first_name,
      client_last_name: appointment.client_last_name,
      client_phone: appointment.client_phone,
      client_email: appointment.client_email || '',
      therapist_id: appointment.therapist_id,
      service_id: appointment.service_id,
      start_time: localDateTime,
      status: appointment.status,
      body_map_gender: appointment.body_map_gender || '',
      body_map_points: appointment.body_map_points || [],
    });
    setShowModal(true);
  };

  const handleCompleteAppointment = async (id) => {
    try {
      await appointmentService.updateStatus(id, 'completed');
      fetchData();
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Greška pri ažuriranju statusa');
    }
  };

  const handleQuickBook = (time, therapistId) => {
    const dateTime = `${selectedDate}T${time}`;
    setFormData({
      ...formData,
      start_time: dateTime,
      therapist_id: therapistId || '',
    });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingAppointment(null);
    setFormData({
      client_first_name: '',
      client_last_name: '',
      client_phone: '',
      client_email: '',
      therapist_id: '',
      service_id: '',
      start_time: '',
      status: 'scheduled',
      body_map_gender: '',
      body_map_points: [],
    });
  };

  const handlePrintClick = (appointment) => {
    setAppointmentToPrint(appointment);
    setShowLanguageModal(true);
  };

  const handleLanguageSelect = (language) => {
    if (appointmentToPrint) {
      handlePrintMassageSheet(appointmentToPrint, language);
    }
    setShowLanguageModal(false);
    setAppointmentToPrint(null);
  };

  const handlePrintMassageSheet = (appointment, language = 'sr') => {
    const printWindow = window.open('', '_blank');
    const serviceName = getServiceName(appointment.service_id);
    const therapistName = getTherapistName(appointment.therapist_id);
    const appointmentDate = formatDateToDDMMYYYY(appointment.start_time.split('T')[0]);
    const appointmentTime = formatTime(appointment.start_time);
    const appointmentEndTime = formatTime(appointment.end_time);
    const t = translations[language];

    // Generate body maps with real images
    const generateBodyMaps = () => {
      const bodyImages = {
        male: {
          front: process.env.REACT_APP_BODY_MALE_FRONT,
          back: process.env.REACT_APP_BODY_MALE_BACK
        },
        female: {
          front: process.env.REACT_APP_BODY_FEMALE_FRONT,
          back: process.env.REACT_APP_BODY_FEMALE_BACK
        }
      };
      
      const frontPoints = (appointment.body_map_points || []).filter(p => p.side === 'front');
      const backPoints = (appointment.body_map_points || []).filter(p => p.side === 'back');
      
      const frontImageUrl = bodyImages[appointment.body_map_gender]?.front;
      const backImageUrl = bodyImages[appointment.body_map_gender]?.back;

      const renderPoints = (points) => {
        return points.map(point => `
          <div style="position: absolute; left: ${point.x}%; top: ${point.y}%; transform: translate(-50%, -50%);">
            <div style="width: 16px; height: 16px; border-radius: 50%; background-color: #ef4444; border: 2px solid #991b1b; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>
          </div>
        `).join('');
      };

      return `
        <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 30px;">
          <div style="text-align: center;">
            <h3 style="color: #78350f; margin-bottom: 15px; font-size: 18px;">${t.frontSide}</h3>
            <div style="position: relative; width: 250px; height: 500px; border: 2px solid #d97706; border-radius: 8px; overflow: hidden; background: white; display: flex; align-items: center; justify-content: center;">
              <div style="position: relative; width: 100%; height: 100%;">
                <img src="${frontImageUrl}" alt="Front" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); max-width: 100%; max-height: 100%; object-fit: contain;" />
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                  ${renderPoints(frontPoints)}
                </div>
              </div>
            </div>
            <p style="margin-top: 10px; color: #92400e; font-weight: bold;">${frontPoints.length} ${t.markedPoints}</p>
          </div>
          
          <div style="text-align: center;">
            <h3 style="color: #78350f; margin-bottom: 15px; font-size: 18px;">${t.backSide}</h3>
            <div style="position: relative; width: 250px; height: 500px; border: 2px solid #d97706; border-radius: 8px; overflow: hidden; background: white; display: flex; align-items: center; justify-content: center;">
              <div style="position: relative; width: 100%; height: 100%;">
                <img src="${backImageUrl}" alt="Back" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); max-width: 100%; max-height: 100%; object-fit: contain;" />
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                  ${renderPoints(backPoints)}
                </div>
              </div>
            </div>
            <p style="margin-top: 10px; color: #92400e; font-weight: bold;">${backPoints.length} ${t.markedPoints}</p>
          </div>
        </div>
      `;
    };

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>List za masažu - ${appointment.client_first_name} ${appointment.client_last_name}</title>
        <style>
          @page {
            size: A4;
            margin: 2cm;
          }
          body {
            font-family: 'Arial', sans-serif;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
          }
          .header {
            text-align: center;
            border-bottom: 3px solid #d97706;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .header img {
            max-width: 200px;
            height: auto;
            margin-bottom: 15px;
          }
          .header h1 {
            color: #92400e;
            margin: 10px 0;
            font-size: 28px;
          }
          .info-section {
            background: #fef3c7;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #d97706;
          }
          .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #fde68a;
          }
          .info-label {
            font-weight: bold;
            color: #78350f;
          }
          .info-value {
            color: #92400e;
          }
          .body-map-section {
            margin-top: 30px;
            text-align: center;
          }
          .body-map-section h2 {
            color: #78350f;
            margin-bottom: 20px;
          }
          .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #fde68a;
            text-align: center;
            color: #d97706;
            font-size: 12px;
          }
          @media print {
            body {
              padding: 0;
            }
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <img src="${process.env.REACT_APP_LOGO_URL}" alt="Bua Luang Thai Spa Logo" />
          <h1>Bua Luang Thai Spa</h1>
          <p style="color: #92400e; margin: 0; font-size: 16px;">${t.title}</p>
        </div>

        <div class="info-section">
          <div class="info-row">
            <span class="info-label">${t.client}</span>
            <span class="info-value">${appointment.client_first_name} ${appointment.client_last_name}</span>
          </div>
          <div class="info-row">
            <span class="info-label">${t.appointmentDate}</span>
            <span class="info-value">${appointmentDate}</span>
          </div>
          <div class="info-row">
            <span class="info-label">${t.time}</span>
            <span class="info-value">${appointmentTime} - ${appointmentEndTime}</span>
          </div>
          <div class="info-row">
            <span class="info-label">${t.service}</span>
            <span class="info-value">${serviceName}</span>
          </div>
          <div class="info-row">
            <span class="info-label">${t.therapist}</span>
            <span class="info-value">${therapistName}</span>
          </div>
        </div>

        <div class="body-map-section">
          <h2 style="color: #78350f; margin-bottom: 20px; text-align: center;">${t.bodyMap}</h2>
          ${appointment.body_map_gender ? generateBodyMaps() : '<p style="text-align: center; color: #999;">Nema mape tela</p>'}
          ${(appointment.body_map_points && appointment.body_map_points.length > 0) ? `
            <p style="margin-top: 30px; text-align: center; color: #92400e; font-weight: bold; font-size: 16px;">
              Ukupno označenih oblasti: ${appointment.body_map_points.length}
            </p>
          ` : ''}
        </div>

        <div class="footer">
          <p>Dokument kreiran: ${new Date().toLocaleString('sr-RS')}</p>
          <p>© Bua Luang Thai Spa</p>
        </div>

        <div class="no-print" style="text-align: center; margin-top: 30px;">
          <button onclick="window.print()" style="background: #4f46e5; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
            🖨️ Štampaj
          </button>
          <button onclick="window.close()" style="background: #6b7280; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; margin-left: 10px;">
            ✖ Zatvori
          </button>
        </div>
      </body>
      </html>
    `;

    printWindow.document.write(html);
    printWindow.document.close();
  };

  const getTherapistName = (id) => {
    const therapist = therapists.find((t) => t.id === id);
    return therapist?.name || 'Unknown';
  };

  const getServiceName = (id) => {
    const service = services.find((s) => s.id === id);
    return service?.name || 'Unknown';
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit' });
  };

  const changeDate = (days) => {
    const currentDate = new Date(selectedDate);
    currentDate.setDate(currentDate.getDate() + days);
    setSelectedDate(currentDate.toISOString().split('T')[0]);
  };

  const generateTimeSlots = () => {
    if (!businessHours) return [];
    
    const slots = [];
    const [startHour, startMin] = businessHours.start_time.split(':').map(Number);
    const [endHour, endMin] = businessHours.end_time.split(':').map(Number);
    
    let currentHour = startHour;
    let currentMin = startMin;
    
    while (currentHour < endHour || (currentHour === endHour && currentMin < endMin)) {
      const timeStr = `${String(currentHour).padStart(2, '0')}:${String(currentMin).padStart(2, '0')}`;
      slots.push(timeStr);
      
      currentMin += businessHours.slot_duration;
      if (currentMin >= 60) {
        currentHour += Math.floor(currentMin / 60);
        currentMin = currentMin % 60;
      }
    }
    
    return slots;
  };

  const isSlotOccupied = (time, therapistId) => {
    return appointments.some(apt => {
      if (apt.therapist_id !== therapistId || apt.status === 'cancelled') return false;
      
      const aptStart = new Date(apt.start_time);
      const aptEnd = new Date(apt.end_time);
      const slotTime = new Date(`${selectedDate}T${time}`);
      
      return slotTime >= aptStart && slotTime < aptEnd;
    });
  };

  const getAppointmentAtSlot = (time, therapistId) => {
    return appointments.find(apt => {
      if (apt.therapist_id !== therapistId) return false;
      
      const aptStart = new Date(apt.start_time);
      const slotTime = new Date(`${selectedDate}T${time}`);
      
      return Math.abs(aptStart - slotTime) < 60000; // Within 1 minute
    });
  };

  const statusLabels = {
    scheduled: 'Zakazan',
    completed: 'Završen',
    cancelled: 'Otkazan',
  };

  const statusColors = {
    scheduled: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  const timeSlots = generateTimeSlots();

  return (
    <div className="min-h-screen bg-gray-50 py-4 md:py-8 overflow-x-hidden" data-testid="appointments-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900" data-testid="appointments-title">
              Termini
            </h1>
            <p className="mt-2 text-gray-600">Upravljanje terminima i zakazivanjima</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            data-testid="add-appointment-btn"
          >
            <Plus className="w-5 h-5 mr-2" />
            Zakazite termin
          </button>
        </div>

        {/* Date Navigation & View Toggle */}
        <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => changeDate(-1)}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              data-testid="prev-day-btn"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5 text-gray-500" />
              <div className="relative">
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 opacity-0 absolute w-40"
                  data-testid="date-picker"
                />
                <div className="px-4 py-2 border border-gray-300 rounded-lg w-40 text-center font-medium bg-white pointer-events-none">
                  {formatDateToDDMMYYYY(selectedDate)}
                </div>
              </div>
            </div>
            <button
              onClick={() => changeDate(1)}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              data-testid="next-day-btn"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              data-testid="list-view-btn"
            >
              Lista
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'calendar'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              data-testid="calendar-view-btn"
            >
              Kalendar
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12" data-testid="appointments-loading">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : viewMode === 'list' ? (
          /* List View */
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vreme
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Klijent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Kontakt
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usluga
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Terapeut
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Akcije
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {appointments.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                      Nema zakazanih termina za ovaj dan.
                    </td>
                  </tr>
                ) : (
                  appointments.map((appointment) => (
                    <tr key={appointment.id} data-testid={`appointment-row-${appointment.id}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {formatTime(appointment.start_time)} - {formatTime(appointment.end_time)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {appointment.client_first_name} {appointment.client_last_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{appointment.client_phone}</div>
                        {appointment.client_email && (
                          <div className="text-xs text-gray-500">{appointment.client_email}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <div className="text-sm text-gray-900">
                            {getServiceName(appointment.service_id)}
                          </div>
                          {(() => {
                            const service = services.find(s => s.id === appointment.service_id);
                            const discount = service?.discount_percentage || 0;
                            if (discount > 0) {
                              return (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/>
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd"/>
                                  </svg>
                                  -{discount}%
                                </span>
                              );
                            }
                            return null;
                          })()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {getTherapistName(appointment.therapist_id)}
                        </div>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            statusColors[appointment.status]
                          }`}
                        >
                          {statusLabels[appointment.status]}
                        </span>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {appointment.body_map_gender && (
                          <button
                            onClick={() => handlePrintClick(appointment)}
                            className="text-purple-600 hover:text-purple-900 mr-4"
                            data-testid={`print-appointment-${appointment.id}`}
                            title="Štampaj list za masažu"
                          >
                            <Printer className="w-5 h-5" />
                          </button>
                        )}
                        {appointment.status === 'scheduled' && (
                          <button
                            onClick={() => handleCompleteAppointment(appointment.id)}
                            className="text-green-600 hover:text-green-900 mr-4"
                            data-testid={`complete-appointment-${appointment.id}`}
                            title="Označi kao završeno"
                          >
                            <Check className="w-5 h-5" />
                          </button>
                        )}
                        <button
                          onClick={() => handleEdit(appointment)}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                          data-testid={`edit-appointment-${appointment.id}`}
                        >
                          <Edit2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(appointment.id)}
                          className="text-red-600 hover:text-red-900"
                          data-testid={`delete-appointment-${appointment.id}`}
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : (
          /* Calendar View */
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto scroll-container">
              <table className="min-w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50">
                      Vreme
                    </th>
                    {therapists.map((therapist) => (
                      <th
                        key={therapist.id}
                        className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[150px]"
                      >
                        {therapist.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {timeSlots.map((time) => (
                    <tr key={time} className="hover:bg-gray-50">
                      <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-white border-r">
                        {time}
                      </td>
                      {therapists.map((therapist) => {
                        const appointment = getAppointmentAtSlot(time, therapist.id);
                        const isOccupied = isSlotOccupied(time, therapist.id);
                        
                        return (
                          <td
                            key={`${time}-${therapist.id}`}
                            className={`px-2 py-2 text-center text-sm cursor-pointer ${
                              isOccupied ? 'bg-blue-100' : 'hover:bg-green-50'
                            }`}
                            onClick={() => !isOccupied && handleQuickBook(time, therapist.id)}
                            data-testid={`slot-${time}-${therapist.id}`}
                          >
                            {appointment ? (
                              <div
                                className="bg-blue-600 text-white rounded p-2 text-xs"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleEdit(appointment);
                                }}
                              >
                                <div className="font-semibold">
                                  {appointment.client_first_name} {appointment.client_last_name}
                                </div>
                                <div className="text-xs opacity-90">
                                  {getServiceName(appointment.service_id)}
                                </div>
                              </div>
                            ) : (
                              <div className="text-gray-400 text-xs">Slobodno</div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-6 py-4 bg-gray-50 border-t">
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-600 rounded"></div>
                  <span>Zauzeto</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-white border border-gray-300 rounded"></div>
                  <span>Slobodno (kliknite za zakazivanje)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          data-testid="appointment-modal"
        >
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingAppointment ? 'Izmeni termin' : 'Zakazite termin'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
                data-testid="close-modal-btn"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} data-testid="appointment-form">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ime *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.client_first_name}
                      onChange={(e) =>
                        setFormData({ ...formData, client_first_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-firstname-input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Prezime *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.client_last_name}
                      onChange={(e) =>
                        setFormData({ ...formData, client_last_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-lastname-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Telefon *
                    </label>
                    <input
                      type="tel"
                      required
                      value={formData.client_phone}
                      onChange={(e) =>
                        setFormData({ ...formData, client_phone: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-phone-input"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={formData.client_email}
                      onChange={(e) =>
                        setFormData({ ...formData, client_email: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="client-email-input"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Usluga *
                  </label>
                  <select
                    required
                    value={formData.service_id}
                    onChange={(e) => setFormData({ ...formData, service_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="service-select"
                  >
                    <option value="">Izaberite uslugu</option>
                    {services.map((service) => (
                      <option key={service.id} value={service.id}>
                        {service.name} - {service.duration} min - {service.price} RSD
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Terapeut *
                  </label>
                  <select
                    required
                    value={formData.therapist_id}
                    onChange={(e) => setFormData({ ...formData, therapist_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="therapist-select"
                  >
                    <option value="">Izaberite terapeuta</option>
                    {therapists.map((therapist) => (
                      <option key={therapist.id} value={therapist.id}>
                        {therapist.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Datum i vreme početka *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    data-testid="start-time-input"
                  />
                </div>

                {editingAppointment && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      data-testid="status-select"
                    >
                      <option value="scheduled">Zakazan</option>
                      <option value="completed">Završen</option>
                      <option value="cancelled">Otkazan</option>
                    </select>
                  </div>
                )}

                {/* Body Map Section */}
                <div className="col-span-2 mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Mapa tela za masažu (opciono)
                  </h3>
                  <BodyMap
                    gender={formData.body_map_gender}
                    onGenderChange={(gender) => setFormData({ ...formData, body_map_gender: gender })}
                    points={formData.body_map_points}
                    onPointsChange={(points) => setFormData({ ...formData, body_map_points: points })}
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                  data-testid="save-appointment-btn"
                >
                  Sačuvaj
                </button>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                  data-testid="cancel-appointment-btn"
                >
                  Otkaži
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Language Selection Modal for Print */}
      {showLanguageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">
              Izaberite jezik za štampu / เลือกภาษาสำหรับการพิมพ์
            </h3>
            <p className="text-sm text-gray-600 mb-6 text-center">
              Kliknite na željeni jezik ispod
            </p>
            
            <div className="flex flex-col gap-3">
              <button
                onClick={() => handleLanguageSelect('sr')}
                className="w-full py-4 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-lg transition-colors flex items-center justify-center gap-3"
              >
                <span className="text-2xl">🇷🇸</span>
                <span>Srpski</span>
              </button>
              
              <button
                onClick={() => handleLanguageSelect('th')}
                className="w-full py-4 px-6 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold text-lg transition-colors flex items-center justify-center gap-3"
              >
                <span className="text-2xl">🇹🇭</span>
                <span>ภาษาไทย (Thai)</span>
              </button>
            </div>

            <button
              onClick={() => setShowLanguageModal(false)}
              className="mt-4 w-full py-2 px-4 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
            >
              Otkaži / ยกเลิก
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Appointments;
