/**
 * Model de persistência para Cursos.
 */

const { dbGet, dbAll } = require('../database/db');

class CourseModel {
  static async findActiveById(id) {
    return await dbGet("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
  }

  static async findAll() {
    return await dbAll("SELECT * FROM courses ORDER BY id ASC");
  }
}

module.exports = CourseModel;
