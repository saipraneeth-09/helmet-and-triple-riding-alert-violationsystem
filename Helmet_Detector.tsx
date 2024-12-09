'use client'

import { useRef, useEffect, useState } from 'react'
import * as tf from '@tensorflow/tfjs'
import * as cocossd from '@tensorflow-models/coco-ssd'

interface HelmetDetectorProps {
  onAlert: (message: string) => void
}

export function HelmetDetector({ onAlert }: HelmetDetectorProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [model, setModel] = useState<cocossd.ObjectDetection | null>(null)

  useEffect(() => {
    const loadModel = async () => {
      const loadedModel = await cocossd.load()
      setModel(loadedModel)
    }
    loadModel()
  }, [])

  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream
          }
        })
        .catch(err => console.error("Error accessing webcam:", err))
    }
  }, [])

  useEffect(() => {
    if (!model) return

    const detectObjects = async () => {
      if (videoRef.current && canvasRef.current) {
        const video = videoRef.current
        const canvas = canvasRef.current
        const ctx = canvas.getContext('2d')

        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

          const predictions = await model.detect(video)

          let personCount = 0
          let helmetCount = 0

          predictions.forEach(prediction => {
            if (prediction.class === 'person') {
              personCount++
            } else if (prediction.class === 'helmet') {
              helmetCount++
            }

            ctx.beginPath()
            ctx.rect(...prediction.bbox)
            ctx.lineWidth = 2
            ctx.strokeStyle = 'red'
            ctx.fillStyle = 'red'
            ctx.stroke()
            ctx.fillText(
              `${prediction.class} (${Math.round(prediction.score * 100)}%)`,
              prediction.bbox[0],
              prediction.bbox[1] > 10 ? prediction.bbox[1] - 5 : 10
            )
          })

          if (personCount > 1) {
            onAlert("Multiple riders detected!")
          }
          if (personCount > 0 && helmetCount === 0) {
            onAlert("No helmet detected!")
          }
        }
      }
      requestAnimationFrame(detectObjects)
    }

    detectObjects()
  }, [model, onAlert])

  return (
    <div className="relative">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        width="640"
        height="480"
        className="hidden"
      />
      <canvas
        ref={canvasRef}
        width="640"
        height="480"
        className="border border-gray-300"
      />
    </div>
  )
}

