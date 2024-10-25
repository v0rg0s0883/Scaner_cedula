'use Lector'

import { useState, useRef, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Camera } from 'lucide-react'
import { Progress } from "@/components/ui/progress"
import { createWorker } from 'tesseract.js'

interface DatosCedula {
  numeroCedula: string;
  nombre: string;
  sexo: string;
  fechaNacimiento: string;
  lugarNacimiento: string;
  nombrePadre: string;
  nombreMadre: string;
  domicilioElectoral: string;
  vencimiento: string;
}

export default function Component() {
  const [escaneando, setEscaneando] = useState(false)
  const [datos, setDatos] = useState<Partial<DatosCedula>>({})
  const [progreso, setProgreso] = useState(0)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const workerRef = useRef<Tesseract.Worker | null>(null)

  useEffect(() => {
    const inicializarWorker = async () => {
      workerRef.current = await createWorker('spa')
    }
    inicializarWorker()

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate()
      }
    }
  }, [])

  useEffect(() => {
    let stream: MediaStream | null = null;
    let frameId: number;

    const iniciarCamara = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        console.error("Error al acceder a la cámara:", err)
      }
    }

    const procesarFrame = async () => {
      if (videoRef.current && canvasRef.current && workerRef.current) {
        const ctx = canvasRef.current.getContext('2d')
        if (ctx) {
          ctx.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height)
          const imageData = canvasRef.current.toDataURL('image/jpeg')
          await realizarOCR(imageData)
        }
      }
      frameId = requestAnimationFrame(procesarFrame)
    }

    if (escaneando) {
      iniciarCamara()
      frameId = requestAnimationFrame(procesarFrame)
    } else {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
      setDatos({})
      setProgreso(0)
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
      if (frameId) {
        cancelAnimationFrame(frameId)
      }
    }
  }, [escaneando])

  const realizarOCR = async (imageData: string) => {
    if (!workerRef.current) return

    try {
      const { data: { text } } = await workerRef.current.recognize(imageData)
      extraerDatosCedula(text)
    } catch (error) {
      console.error('Error en OCR:', error)
    }
  }

  const extraerDatosCedula = (texto: string) => {
    const lineas = texto.split('\n')
    const nuevosDatos: Partial<DatosCedula> = {}
    let camposDetectados = 0

    lineas.forEach(linea => {
      if (linea.includes('Número de Cédula:')) {
        nuevosDatos.numeroCedula = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Fecha de Nacimiento:')) {
        nuevosDatos.fechaNacimiento = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Lugar de Nacimiento:')) {
        nuevosDatos.lugarNacimiento = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Nombre del Padre:')) {
        nuevosDatos.nombrePadre = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Nombre de la Madre:')) {
        nuevosDatos.nombreMadre = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Domicilio Electoral:')) {
        nuevosDatos.domicilioElectoral = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.includes('Vencimiento:')) {
        nuevosDatos.vencimiento = linea.split(':')[1].trim()
        camposDetectados++
      } else if (linea.match(/^[A-Z\s]+$/)) {
        // Asumimos que una línea con solo letras mayúsculas y espacios es el nombre
        nuevosDatos.nombre = linea.trim()
        camposDetectados++
      } else if (linea.match(/^(MASCULINO|FEMENINO)$/i)) {
        nuevosDatos.sexo = linea.trim()
        camposDetectados++
      }
    })

    setDatos(prevDatos => ({ ...prevDatos, ...nuevosDatos }))
    setProgreso(Math.min((camposDetectados / 9) * 100, 100))
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Lector de Cédula Costarricense</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="escaneo-switch"
              checked={escaneando}
              onCheckedChange={setEscaneando}
            />
            <Label htmlFor="escaneo-switch">
              {escaneando ? 'Detener escaneo' : 'Iniciar escaneo'}
            </Label>
          </div>
          
          <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
            {!escaneando && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Camera className="w-16 h-16 text-gray-400" />
              </div>
            )}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${!escaneando ? 'hidden' : ''}`}
            />
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 w-full h-full"
              width={640}
              height={480}
            />
            {escaneando && progreso < 100 && (
              <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center bg-black bg-opacity-50">
                <AlertCircle className="text-yellow-400 w-16 h-16 animate-pulse" />
              </div>
            )}
            {progreso === 100 && (
              <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center bg-black bg-opacity-50">
                <CheckCircle2 className="text-green-400 w-16 h-16" />
              </div>
            )}
          </div>
          
          <Progress value={progreso} className="w-full" />
          
          <div className="mt-4 space-y-2">
            <h3 className="text-lg font-semibold">Datos detectados:</h3>
            <p><strong>Número de Cédula:</strong> {datos.numeroCedula || 'Escaneando...'}</p>
            <p><strong>Nombre:</strong> {datos.nombre || 'Escaneando...'}</p>
            <p><strong>Sexo:</strong> {datos.sexo || 'Escaneando...'}</p>
            <p><strong>Fecha de Nacimiento:</strong> {datos.fechaNacimiento || 'Escaneando...'}</p>
            <p><strong>Lugar de Nacimiento:</strong> {datos.lugarNacimiento || 'Escaneando...'}</p>
            <p><strong>Nombre del Padre:</strong> {datos.nombrePadre || 'Escaneando...'}</p>
            <p><strong>Nombre de la Madre:</strong> {datos.nombreMadre || 'Escaneando...'}</p>
            <p><strong>Domicilio Electoral:</strong> {datos.domicilioElectoral || 'Escaneando...'}</p>
            <p><strong>Vencimiento:</strong> {datos.vencimiento || 'Escaneando...'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
