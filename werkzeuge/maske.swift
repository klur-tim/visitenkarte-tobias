// Stellt die Person im Foto frei (Apple Vision, läuft lokal) und speichert eine Graustufen-Maske.
// Aufruf: swift maske.swift <eingabe.jpg> <maske.png>
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count == 3 else { print("Aufruf: swift maske.swift <eingabe> <maske.png>"); exit(1) }
let inURL = URL(fileURLWithPath: args[1]), outURL = URL(fileURLWithPath: args[2])
guard let ci = CIImage(contentsOf: inURL) else { print("Bild nicht lesbar"); exit(1) }

let handler = VNImageRequestHandler(ciImage: ci, options: [:])
let req = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([req])
guard let obs = req.results?.first else { print("Keine Person gefunden"); exit(1) }
let buf = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: buf)
let ctx = CIContext()
guard let cg = ctx.createCGImage(mask, from: mask.extent) else { exit(1) }
let rep = NSBitmapImageRep(cgImage: cg)
try rep.representation(using: .png, properties: [:])!.write(to: outURL)
print("Maske gespeichert: \(Int(mask.extent.width))x\(Int(mask.extent.height))")
